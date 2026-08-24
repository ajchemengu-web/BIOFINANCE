"""Transaction history lookups (docs/database-schema.md)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bioid import BioID
from app.models.transaction import PaymentAttempt, Transaction


class TransactionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_user(self, user_id: uuid.UUID) -> list[Transaction]:
        bio_id_result = await self.db.execute(select(BioID).where(BioID.user_id == user_id))
        bio_id = bio_id_result.scalar_one_or_none()
        if bio_id is None:
            return []
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.bio_id == bio_id.id)
            .order_by(Transaction.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, transaction_id: uuid.UUID) -> Transaction | None:
        return await self.db.get(Transaction, transaction_id)

    async def get_attempts(self, transaction_id: uuid.UUID) -> list[PaymentAttempt]:
        result = await self.db.execute(
            select(PaymentAttempt).where(PaymentAttempt.transaction_id == transaction_id)
        )
        return list(result.scalars().all())
