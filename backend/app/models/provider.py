import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class ProviderConnection(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "provider_connections"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    provider_code: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="CONNECTED")


class ProviderAccount(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "provider_accounts"

    provider_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("provider_connections.id")
    )
    external_account_ref: Mapped[str] = mapped_column(String)
    currency: Mapped[str] = mapped_column(String, default="KES")
