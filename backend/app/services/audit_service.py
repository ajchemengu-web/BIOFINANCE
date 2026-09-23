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

Not wired: BIOMETRIC_SUCCESS/BIOMETRIC_FAILED (biometric auth happens
entirely client-side — docs/security-model.md, "raw biometric data never
leaves the device" — there's no backend signal to log; a client self-report
would be exactly the anti-pattern that principle rules out) and
DEVICE_REMOVED (no device-removal endpoint exists yet). Both noted in
docs/roadmap.md rather than faked.

log() never commits — it stages the row so it lands in the same
transaction as whatever it's auditing, via that caller's own commit. An
event that never gets to a commit (e.g. the surrounding operation raises
first) simply never persists, same as any other pending row in that
session — there's nothing here to roll back separately.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def log(self, event_type: str, user_id: uuid.UUID | None = None, **metadata) -> None:
        """metadata is reference IDs and statuses only — never a secret,
        never raw biometric data (docs/security-model.md)."""
        self.db.add(AuditEvent(user_id=user_id, event_type=event_type, event_metadata=metadata))
