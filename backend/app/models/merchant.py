import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class Merchant(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "merchants"

    business_name: Mapped[str] = mapped_column(String)
    merchant_code: Mapped[str] = mapped_column(String, unique=True, index=True)
    # Nullable rather than backfilled — a merchant row created before real
    # merchant auth existed (migration 0005) has no credential and simply
    # can't log in; nothing in this MVP depended on merchants having one
    # before now. Every row POST /merchants/register creates has both.
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")


class MerchantDevice(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "merchant_devices"

    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    device_identifier: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")
