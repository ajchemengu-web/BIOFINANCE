import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin, UpdatedAtMixin


class Transaction(Base, UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "transactions"

    # Null until claimed — merchant-initiated requests (biopos/) have no
    # customer identified yet when the row is created. See payment_service.py.
    bio_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bio_ids.id"), nullable=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String, default="KES")
    status: Mapped[str] = mapped_column(String, default="CREATED")
    selected_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String, unique=True, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PaymentAttempt(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "payment_attempts"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id")
    )
    provider_code: Mapped[str] = mapped_column(String)
    result: Mapped[str] = mapped_column(String)
    provider_reference: Mapped[str | None] = mapped_column(String, nullable=True)
