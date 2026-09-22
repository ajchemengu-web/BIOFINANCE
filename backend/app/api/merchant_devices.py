from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_merchant
from app.db.database import get_db
from app.models.merchant import Merchant
from app.schemas.merchant_devices import MerchantDeviceRegisterRequest, MerchantDeviceResponse
from app.services.merchant_device_service import MerchantDeviceService

router = APIRouter(prefix="/merchant-devices", tags=["merchant-devices"])


@router.post("/register", response_model=MerchantDeviceResponse)
async def register_merchant_device(
    payload: MerchantDeviceRegisterRequest,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    """
    Self-service, same trust model as POST /devices/register on the
    customer side: any authenticated merchant can register any
    device_identifier for itself. Upserts — re-registering an existing
    device_identifier re-activates it rather than erroring, so a
    previously REVOKED terminal can be brought back without a separate
    endpoint. See app/services/merchant_device_service.py.
    """
    return await MerchantDeviceService(db).register(merchant.id, payload.device_identifier)
