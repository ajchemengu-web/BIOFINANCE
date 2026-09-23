"""Payment lifecycle: idempotency, routing, and the transaction state machine
(docs/database-schema.md).

Two ways a Transaction gets created, per the two apps that create them:
- create_payment (mobile/, the customer's own app): the customer has
  already authenticated client-side by the time this is called, so the
  transaction goes straight to AUTHENTICATED and routes immediately.
- create_payment_request + claim_payment_request (biopos/, the merchant
  terminal): the merchant creates a request. Two variants (docs/roadmap.md
  Phase 5, "BioFinance ID push pairing"):
    - open claim (no bio_id_code): bio_id stays null until whoever calls
      claim first, with a valid session, attaches theirs.
    - BioFinance-ID-targeted (bio_id_code given): bio_id is resolved and
      attached right away, but the row still sits in AUTHENTICATION_PENDING
      — attaching identity isn't authenticating it. claim_payment_request
      then requires the claiming session's bio_id to match the one already
      on the row, rejecting anyone else.
  Either way, claim_payment_request is what actually authenticates and
  routes it.
Both paths converge on _route_and_resolve so BioRouter behaves identically
regardless of which app originated the transaction.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.rate_limit import SlidingWindowRateLimiter
from app.models.bioid import BioID
from app.models.merchant import Merchant
from app.models.provider import ProviderAccount, ProviderConnection
from app.models.routing_policy import RoutingPolicy
from app.models.transaction import PaymentAttempt, Transaction
from app.services.audit_service import AuditService
from app.services.device_service import DeviceService
from app.services.push_service import PushService
from app.services.router_service import RouterService

_CANCELLABLE_STATUSES = {"CREATED", "AUTHENTICATION_PENDING", "AUTHENTICATED", "ROUTING"}

# BioFinance ID push pairing's abuse surface (docs/security-model.md,
# "Abuse surface: unsolicited push spam") — only guards the targeted path
# (bio_id_code given), not the open-request path, which has no BioFinance
# ID to spam pushes against in the first place.
_bio_id_code_rate_limiter = SlidingWindowRateLimiter(limit=5, window_seconds=60)
_merchant_targeted_request_rate_limiter = SlidingWindowRateLimiter(limit=20, window_seconds=60)

# "Suspicious-transaction logging" (docs/security-model.md "Fraud
# protection (MVP scope)") — a fixed count/window rule, not behavioral
# modeling (explicitly deferred in the same doc). Values are a starting
# point to tune, not derived from real fraud data.
_SUSPICIOUS_FAILURE_THRESHOLD = 3
_SUSPICIOUS_FAILURE_WINDOW_SECONDS = 600


class PaymentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.router = RouterService()

    async def create_payment(
        self,
        user_id: uuid.UUID,
        merchant_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> Transaction:
        existing = await self._find_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing

        self._require_within_transaction_limit(amount)
        bio_id = await self._require_bio_id(user_id)

        transaction = Transaction(
            bio_id=bio_id.id,
            merchant_id=merchant_id,
            amount=amount,
            currency=currency,
            status="AUTHENTICATED",  # biometric auth already verified client-side before this call
            idempotency_key=idempotency_key,
        )
        self.db.add(transaction)
        await self.db.flush()
        audit = AuditService(self.db)
        audit.log("PAYMENT_CREATED", user_id=user_id, transaction_id=str(transaction.id), merchant_id=str(merchant_id))
        audit.log("PAYMENT_AUTHORIZED", user_id=user_id, transaction_id=str(transaction.id))

        return await self._route_and_resolve(transaction, user_id)

    async def create_payment_request(
        self,
        merchant_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        bio_id_code: str | None = None,
    ) -> Transaction:
        """
        Merchant-initiated (biopos/). With no bio_id_code, bio_id is null
        until claim_payment_request attaches one (open claim). With a
        bio_id_code — the merchant read it off the customer at the till,
        STK-Push-style — it's resolved now and attached immediately, so
        the request is targeted at that customer specifically (docs/
        security-model.md, "BioFinance ID push pairing"), and an advisory
        push notification goes out to their registered devices (best-effort
        — see _send_push_pairing_notification). Either way the row starts
        AUTHENTICATION_PENDING: attaching an identity isn't the same as
        authenticating it, and there's no routing policy to route against
        until a real session claims it.
        """
        existing = await self._find_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing

        self._require_within_transaction_limit(amount)

        target_bio_id: BioID | None = None
        if bio_id_code is not None:
            _bio_id_code_rate_limiter.check(bio_id_code)
            _merchant_targeted_request_rate_limiter.check(str(merchant_id))

            bio_id_result = await self.db.execute(select(BioID).where(BioID.code == bio_id_code))
            target_bio_id = bio_id_result.scalar_one_or_none()
            if target_bio_id is None:
                raise LookupError("No BioFinance ID matches that code")

        transaction = Transaction(
            bio_id=target_bio_id.id if target_bio_id else None,
            merchant_id=merchant_id,
            amount=amount,
            currency=currency,
            status="AUTHENTICATION_PENDING",
            idempotency_key=idempotency_key,
        )
        self.db.add(transaction)
        await self.db.flush()
        AuditService(self.db).log(
            "PAYMENT_CREATED",
            user_id=target_bio_id.user_id if target_bio_id else None,
            transaction_id=str(transaction.id),
            merchant_id=str(merchant_id),
        )
        await self.db.commit()
        await self.db.refresh(transaction)

        if target_bio_id is not None:
            await self._send_push_pairing_notification(transaction, target_bio_id)

        return transaction

    async def _send_push_pairing_notification(self, transaction: Transaction, bio_id: BioID) -> None:
        """
        Best-effort advisory push (docs/security-model.md, "The push
        notification is advisory only") — never raises, never blocks the
        request's creation. GET /payments/pending is the fallback if this
        doesn't reach the customer (no token registered, delivery failure,
        FCM not configured at all).
        """
        settings = get_settings()
        if not settings.fcm_configured:
            return

        push_tokens = await DeviceService(self.db).list_push_tokens(bio_id.user_id)
        if not push_tokens:
            return

        merchant = await self.db.get(Merchant, transaction.merchant_id)
        merchant_name = merchant.business_name if merchant else "A merchant"

        push_service = PushService(settings)
        for token in push_tokens:
            await push_service.send_payment_approval_request(
                push_token=token,
                transaction_id=str(transaction.id),
                merchant_name=merchant_name,
                amount=transaction.amount,
                currency=transaction.currency,
            )

    async def claim_payment_request(self, transaction_id: uuid.UUID, user_id: uuid.UUID) -> Transaction:
        """
        A customer, authenticated in their own session, fulfills a
        merchant-created request (POST /payments/{id}/claim).

        If the request was opened with a bio_id_code (BioFinance ID push
        pairing), only the session belonging to that exact bio_id may
        claim it — anyone else gets PermissionError, mapped to 403 by the
        API layer. If it was opened without one (open claim, still around
        for the QR/legacy path), whoever claims it first with a valid
        session gets it, as before — see docs/security-model.md for why
        that path alone isn't production-safe.
        """
        transaction = await self.db.get(Transaction, transaction_id)
        if transaction is None:
            raise LookupError("Payment request not found")
        if transaction.status != "AUTHENTICATION_PENDING":
            raise ValueError("Payment request is not awaiting a customer")

        bio_id = await self._require_bio_id(user_id)

        if transaction.bio_id is not None:
            if transaction.bio_id != bio_id.id:
                raise PermissionError("This payment request was opened for a different BioFinance ID")
        else:
            transaction.bio_id = bio_id.id

        transaction.status = "AUTHENTICATED"
        AuditService(self.db).log("PAYMENT_AUTHORIZED", user_id=user_id, transaction_id=str(transaction.id))
        await self.db.flush()

        return await self._route_and_resolve(transaction, user_id)

    async def _route_and_resolve(self, transaction: Transaction, user_id: uuid.UUID) -> Transaction:
        policy_result = await self.db.execute(
            select(RoutingPolicy).where(RoutingPolicy.user_id == user_id)
        )
        policy = policy_result.scalar_one_or_none()

        if policy is None:
            transaction.status = "PROVIDER_UNAVAILABLE"
            await self._log_payment_failed(user_id, str(transaction.id), transaction.status)
            await self.db.commit()
            await self.db.refresh(transaction)
            return transaction

        transaction.status = "ROUTING"
        connections_by_id, account_ref_by_connection_id = await self._load_candidates(policy)

        transaction.status = "AUTHORIZATION_PENDING"
        attempts = await self.router.route_payment(
            policy,
            connections_by_id,
            account_ref_by_connection_id,
            transaction.amount,
            transaction.currency,
            str(transaction.id),
        )

        transaction.status = "PROCESSING"
        succeeded = False
        pending = False
        for connection, result in attempts:
            self.db.add(
                PaymentAttempt(
                    transaction_id=transaction.id,
                    provider_code=connection.provider_code,
                    result=result.status,
                    provider_reference=result.provider_reference,
                )
            )
            if result.status == "SUCCESS":
                succeeded = True
                transaction.selected_provider = connection.provider_code
            elif result.status == "PENDING":
                pending = True
                transaction.selected_provider = connection.provider_code

        if succeeded:
            transaction.status = "COMPLETED"
            transaction.completed_at = datetime.now(timezone.utc)
        elif pending:
            # Async provider (Daraja) — the STK push reached the phone, but
            # the real outcome only arrives via handle_daraja_callback below.
            # Leaving it here rather than resolving now is the whole point
            # of treating the callback as authoritative (PRD §31).
            transaction.status = "AUTHORIZATION_PENDING"
        elif not attempts:
            transaction.status = "PROVIDER_UNAVAILABLE"
        else:
            transaction.status = "DECLINED"

        if transaction.status == "COMPLETED":
            AuditService(self.db).log(
                "PAYMENT_COMPLETED",
                user_id=user_id,
                transaction_id=str(transaction.id),
                provider=transaction.selected_provider,
            )
        elif transaction.status in ("PROVIDER_UNAVAILABLE", "DECLINED"):
            await self._log_payment_failed(user_id, str(transaction.id), transaction.status)
        # AUTHORIZATION_PENDING (Daraja in flight) logs nothing yet — the
        # eventual outcome is logged by handle_daraja_callback below.

        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    async def handle_daraja_callback(self, checkout_request_id: str, result_code: int) -> Transaction | None:
        """
        Applies Safaricom's STK push callback as the authoritative outcome
        for the matching payment attempt (PRD §31 — never assume the
        initial request succeeded). Returns the updated transaction, or
        None if the callback doesn't match anything BioFinance created
        (e.g. a retry Safaricom sent for a request we already resolved).
        """
        attempt_result = await self.db.execute(
            select(PaymentAttempt).where(PaymentAttempt.provider_reference == checkout_request_id)
        )
        attempt = attempt_result.scalar_one_or_none()
        if attempt is None:
            return None

        transaction = await self.db.get(Transaction, attempt.transaction_id)
        if transaction is None or transaction.status != "AUTHORIZATION_PENDING":
            # Already resolved (e.g. a duplicate callback Safaricom retried)
            # or in a state this shouldn't touch — leave both the attempt
            # and the transaction exactly as they are.
            return transaction

        attempt.result = "SUCCESS" if result_code == 0 else "DECLINED"

        # transaction.bio_id is always set by the time a transaction can
        # reach AUTHORIZATION_PENDING (both create_payment and
        # claim_payment_request set it before routing) — resolved here
        # rather than threaded through as a param, since this is the only
        # caller of handle_daraja_callback and it's a low-frequency webhook,
        # not a hot path.
        bio_id_row = await self.db.get(BioID, transaction.bio_id) if transaction.bio_id else None
        user_id = bio_id_row.user_id if bio_id_row else None

        if result_code == 0:
            transaction.status = "COMPLETED"
            transaction.selected_provider = attempt.provider_code
            transaction.completed_at = datetime.now(timezone.utc)
            AuditService(self.db).log(
                "PAYMENT_COMPLETED", user_id=user_id, transaction_id=str(transaction.id), provider=attempt.provider_code
            )
        else:
            transaction.status = "DECLINED"
            await self._log_payment_failed(user_id, str(transaction.id), transaction.status)

        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    def _require_within_transaction_limit(self, amount: Decimal) -> None:
        """docs/security-model.md 'Fraud protection (MVP scope)' —
        Transaction limits. Per-transaction, not aggregate/daily; the
        latter would need querying a customer's recent transaction
        history, not built here."""
        limit = get_settings().max_transaction_amount
        if amount > limit:
            raise ValueError(f"Amount exceeds the maximum allowed per transaction ({limit})")

    async def _log_payment_failed(self, user_id: uuid.UUID | None, transaction_id: str, status: str) -> None:
        """PAYMENT_FAILED, plus SUSPICIOUS_TRANSACTION when this is the
        Nth failure for this user within a short window — see the
        "suspicious-transaction logging" note in audit_service.py. An
        open merchant request with no customer yet (user_id is None) has
        nothing to count against, so it's skipped rather than logged
        under a null identity."""
        audit = AuditService(self.db)
        audit.log("PAYMENT_FAILED", user_id=user_id, transaction_id=transaction_id, status=status)
        if user_id is None:
            return

        recent_failures = await audit.count_recent("PAYMENT_FAILED", user_id, _SUSPICIOUS_FAILURE_WINDOW_SECONDS)
        if recent_failures >= _SUSPICIOUS_FAILURE_THRESHOLD:
            audit.log(
                "SUSPICIOUS_TRANSACTION",
                user_id=user_id,
                reason="repeated_payment_failures",
                failure_count=recent_failures,
                window_seconds=_SUSPICIOUS_FAILURE_WINDOW_SECONDS,
            )

    async def _find_by_idempotency_key(self, idempotency_key: str) -> Transaction | None:
        existing = await self.db.execute(
            select(Transaction).where(Transaction.idempotency_key == idempotency_key)
        )
        return existing.scalar_one_or_none()

    async def _require_bio_id(self, user_id: uuid.UUID) -> BioID:
        bio_id_result = await self.db.execute(select(BioID).where(BioID.user_id == user_id))
        bio_id = bio_id_result.scalar_one_or_none()
        if bio_id is None:
            raise ValueError("User has no BioID issued")
        return bio_id

    async def _load_candidates(self, policy: RoutingPolicy) -> tuple[dict, dict]:
        connection_ids = [
            provider_id
            for provider_id in (policy.primary_provider_id, policy.fallback_provider_id)
            if provider_id is not None
        ]
        connections_by_id: dict = {}
        account_ref_by_connection_id: dict = {}
        if not connection_ids:
            return connections_by_id, account_ref_by_connection_id

        result = await self.db.execute(
            select(ProviderConnection, ProviderAccount)
            .join(ProviderAccount, ProviderAccount.provider_connection_id == ProviderConnection.id)
            .where(ProviderConnection.id.in_(connection_ids))
        )
        for connection, account in result.all():
            connections_by_id[connection.id] = connection
            account_ref_by_connection_id[connection.id] = account.external_account_ref
        return connections_by_id, account_ref_by_connection_id

    async def get_payment(self, payment_id: uuid.UUID) -> Transaction | None:
        return await self.db.get(Transaction, payment_id)

    async def list_pending_for_user(self, user_id: uuid.UUID) -> list[Transaction]:
        """
        GET /payments/pending — the fallback for BioFinance ID push pairing
        when the push notification never arrives (docs/security-model.md,
        "Delivery isn't guaranteed"). Only ever returns targeted requests
        (bio_id already attached at creation): an open request has bio_id
        null until someone claims it, so it isn't "this user's" to list
        until they've already claimed it — see create_payment_request.
        """
        bio_id = await self._require_bio_id(user_id)
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.bio_id == bio_id.id, Transaction.status == "AUTHENTICATION_PENDING")
            .order_by(Transaction.created_at.desc())
        )
        return list(result.scalars().all())

    async def cancel_payment(self, payment_id: uuid.UUID, merchant_id: uuid.UUID) -> Transaction | None:
        """merchant_id is the authenticated caller's own id (docs/roadmap.md
        Phase 5, "Real merchant authentication") — raises PermissionError,
        mapped to 403 by the API layer, if it doesn't own this request."""
        transaction = await self.db.get(Transaction, payment_id)
        if transaction is None:
            return None
        if transaction.merchant_id != merchant_id:
            raise PermissionError("This payment request belongs to a different merchant")
        if transaction.status in _CANCELLABLE_STATUSES:
            transaction.status = "CANCELLED"
            await self.db.commit()
            await self.db.refresh(transaction)
        return transaction
