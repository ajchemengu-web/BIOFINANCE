"""Device registration — the push-token side of BioFinance ID push pairing.

Upserts on (user_id, device_identifier) rather than always inserting: a
device re-registering (new push token after a reinstall, app restart, token
refresh) should update its existing row, not accumulate duplicates that
push delivery would then fan out to.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.services.audit_service import AuditService


class DeviceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(
        self,
        user_id: uuid.UUID,
        device_identifier: str,
        push_token: str | None,
        platform: str | None,
    ) -> Device:
        result = await self.db.execute(
            select(Device).where(
                Device.user_id == user_id,
                Device.device_identifier == device_identifier,
            )
        )
        device = result.scalar_one_or_none()
        is_new = device is None
        if device is None:
            device = Device(user_id=user_id, device_identifier=device_identifier)
            self.db.add(device)

        device.push_token = push_token
        device.platform = platform
        device.status = "ACTIVE"
        if is_new:
            # Only on first registration, not every push-token refresh —
            # a re-registration isn't a new event worth an audit row.
            AuditService(self.db).log("DEVICE_REGISTERED", user_id=user_id, device_identifier=device_identifier)
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def list_push_tokens(self, user_id: uuid.UUID) -> list[str]:
        """Every ACTIVE device's push token for a user (BioFinance ID push
        pairing sends to all of them — a customer may have more than one)."""
        result = await self.db.execute(
            select(Device.push_token).where(
                Device.user_id == user_id,
                Device.status == "ACTIVE",
                Device.push_token.is_not(None),
            )
        )
        return [token for token in result.scalars().all() if token]
