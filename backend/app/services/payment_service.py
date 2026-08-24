"""Payment lifecycle: idempotency, routing, and the transaction state machine
(docs/database-schema.md)."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bioid import BioID
from app.models.provider import ProviderAccount, ProviderConnection
from app.models.routing_policy import RoutingPolicy
from app.models.transaction import PaymentAttempt, Transaction
from app.services.router_service import RouterService

_CANCELLABLE_STATUSES = {"CREATED", "AUTHENTICATION_PENDING", "AUTHENTICATED", "ROUTING"}


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
        existing = await self.db.execute(
            select(Transaction).where(Transaction.idempotency_key == idempotency_key)
        )
        existing_transaction = existing.scalar_one_or_none()
        if existing_transaction is not None:
            return existing_transaction

        bio_id_result = await self.db.execute(select(BioID).where(BioID.user_id == user_id))
        bio_id = bio_id_result.scalar_one_or_none()
        if bio_id is None:
            raise ValueError("User has no BioID issued")

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

        policy_result = await self.db.execute(
            select(RoutingPolicy).where(RoutingPolicy.user_id == user_id)
        )
        policy = policy_result.scalar_one_or_none()

        if policy is None:
            transaction.status = "PROVIDER_UNAVAILABLE"
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
            amount,
            currency,
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

        if result_code == 0:
            transaction.status = "COMPLETED"
            transaction.selected_provider = attempt.provider_code
            transaction.completed_at = datetime.now(timezone.utc)
        else:
            transaction.status = "DECLINED"

        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

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

    async def cancel_payment(self, payment_id: uuid.UUID) -> Transaction | None:
        transaction = await self.db.get(Transaction, payment_id)
        if transaction is None:
            return None
        if transaction.status in _CANCELLABLE_STATUSES:
            transaction.status = "CANCELLED"
            await self.db.commit()
            await self.db.refresh(transaction)
        return transaction
