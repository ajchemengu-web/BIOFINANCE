import secrets
import string
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.merchant import Merchant
from app.schemas.merchants import MerchantCreateRequest, MerchantResponse

router = APIRouter(prefix="/merchants", tags=["merchants"])


def _generate_merchant_code() -> str:
    return "MC-" + "".join(secrets.choice(string.digits) for _ in range(6))


@router.post("", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
async def create_merchant(payload: MerchantCreateRequest, db: AsyncSession = Depends(get_db)):
    merchant = Merchant(business_name=payload.business_name, merchant_code=_generate_merchant_code())
    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)
    return merchant


@router.get("/{merchant_id}", response_model=MerchantResponse)
async def get_merchant(merchant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    merchant = await db.get(Merchant, merchant_id)
    if merchant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Merchant not found")
    return merchant
