from fastapi import APIRouter, Depends
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
