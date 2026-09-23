"""
merchant_devices enforcement (§33 of the source PRD, docs/security-model.md
"Merchant-side integrity") — the device-level counterpart to merchant
authentication. A merchant token proves *which merchant*; this proves
*which terminal* — a leaked/shared merchant credential alone is no longer
enough to open a payment request, it also has to be called from a device
that merchant has registered.

Mirrors app/services/device_service.py's shape (upsert on identifier, no
unique DB constraint, application-level find-or-create) rather than
inventing a different pattern for the merchant side.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import MerchantDevice


class MerchantDeviceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, merchant_id: uuid.UUID, device_identifier: str) -> MerchantDevice:
        result = await self.db.execute(
            select(MerchantDevice).where(
                MerchantDevice.merchant_id == merchant_id,
                MerchantDevice.device_identifier == device_identifier,
            )
        )
        device = result.scalar_one_or_none()
        if device is None:
            device = MerchantDevice(merchant_id=merchant_id, device_identifier=device_identifier)
            self.db.add(device)

        device.status = "ACTIVE"
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def revoke(self, merchant_id: uuid.UUID, device_id: uuid.UUID) -> MerchantDevice | None:
        """DELETE /merchant-devices/{id} — returns None if the device
        doesn't exist or isn't this merchant's. A revoked terminal
        immediately fails require_registered below (status != ACTIVE), so
        this is the actual mechanism for deactivating a lost/stolen POS
        device, not just bookkeeping."""
        device = await self.db.get(MerchantDevice, device_id)
        if device is None or device.merchant_id != merchant_id:
            return None

        device.status = "REVOKED"
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def require_registered(self, merchant_id: uuid.UUID, device_identifier: str) -> None:
        """Raises PermissionError (mapped to 403 by the API layer) if this
        device isn't a registered, ACTIVE terminal for this merchant."""
        result = await self.db.execute(
            select(MerchantDevice).where(
                MerchantDevice.merchant_id == merchant_id,
                MerchantDevice.device_identifier == device_identifier,
                MerchantDevice.status == "ACTIVE",
            )
        )
        if result.scalar_one_or_none() is None:
            raise PermissionError(
                "This device is not registered to this merchant — register it first via POST /merchant-devices/register"
            )
