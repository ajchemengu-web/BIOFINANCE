import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.devices import DeviceRegisterRequest, DeviceResponse
from app.services.device_service import DeviceService

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/register", response_model=DeviceResponse)
async def register_device(
    payload: DeviceRegisterRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeviceService(db)
    return await service.register(
        user_id=user.id,
        device_identifier=payload.device_identifier,
        push_token=payload.push_token,
        platform=payload.platform,
    )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_device(
    device_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """A lost/replaced phone stops being a push target and, once
    device-level checks exist on the customer side (not built yet — see
    docs/security-model.md "Fraud protection"), would stop being able to
    authorize anything either."""
    device = await DeviceService(db).revoke(user.id, device_id)
    if device is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Device not found")
