"""
Append-only audit trail (docs/security-model.md "Audit logging") — the
audit_events table has existed since the first migration but nothing has
ever written to it until now. Wires the documented minimum event set:

    LOGIN_SUCCESS          LOGIN_FAILED
    DEVICE_REGISTERED      DEVICE_REMOVED
    PROVIDER_CONNECTED     PROVIDER_DISCONNECTED
    ROUTING_CHANGED
    PAYMENT_CREATED        PAYMENT_AUTHORIZED
    PAYMENT_COMPLETED      PAYMENT_FAILED
    BIOID_LOCKED

Plus SUSPICIOUS_TRANSACTION — not in the original documented list, but the
closest achievable reading of "suspicious-transaction logging" under
docs/security-model.md "Fraud protection (MVP scope)": count_recent()
below is a fixed count/window rule (payment_service.py logs it after N
PAYMENT_FAILED events for one user inside a short window), not
statistical or behavioral modeling — that's explicitly deferred in the
same doc.

Not wired, and not fakeable without contradicting this app's own stated
principles: BIOMETRIC_SUCCESS/BIOMETRIC_FAILED, and by extension
"repeated-biometric-failure detection" (docs/security-model.md, "raw
biometric data never leaves the device" — there is no backend signal to
log or to count; a client self-report would be exactly the anti-pattern
that principle rules out).

log() never commits — it stages the row so it lands in the same
transaction as whatever it's auditing, via that caller's own commit. An
event that never gets to a commit (e.g. the surrounding operation raises
first) simply never persists, same as any other pending row in that
session — there's nothing here to roll back separately.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def log(self, event_type: str, user_id: uuid.UUID | None = None, **metadata) -> None:
        """metadata is reference IDs and statuses only — never a secret,
        never raw biometric data (docs/security-model.md)."""
        self.db.add(AuditEvent(user_id=user_id, event_type=event_type, event_metadata=metadata))

    async def count_recent(self, event_type: str, user_id: uuid.UUID, window_seconds: float) -> int:
        """How many event_type rows user_id has within the last
        window_seconds — the building block for "N failures in a row"
        style checks. Session autoflush means a row staged by log() in
        this same request is already visible to this query before the
        caller's own commit, so it counts itself as the Nth event."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        result = await self.db.execute(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.user_id == user_id, AuditEvent.event_type == event_type, AuditEvent.created_at >= cutoff)
        )
        return result.scalar_one()

    async def list_for_user(self, user_id: uuid.UUID, limit: int = 50) -> list[AuditEvent]:
        """GET /audit-events — a user's own activity/security log. Scoped
        strictly to the caller's own user_id; there is no admin/role
        concept anywhere in this app to gate a broader view, and this
        pass doesn't invent one — see docs/roadmap.md."""
        result = await self.db.execute(
            select(AuditEvent)
            .where(AuditEvent.user_id == user_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
