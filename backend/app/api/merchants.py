import uuid

from fastapi import APIRouter, HTTPException, status

from app.schemas.merchants import MerchantResponse

router = APIRouter(prefix="/merchants", tags=["merchants"])

_NOT_IMPLEMENTED = "Implemented starting Phase 5 (BioPOS, docs/roadmap.md)"


@router.get("/{merchant_id}", response_model=MerchantResponse)
async def get_merchant(merchant_id: uuid.UUID):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)
