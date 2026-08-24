import uuid

from fastapi import APIRouter, Header, HTTPException, status

from app.schemas.payments import PaymentCreateRequest, PaymentResponse

router = APIRouter(prefix="/payments", tags=["payments"])

_NOT_IMPLEMENTED = "Implemented in Phase 3 (BioRouter, docs/roadmap.md)"


@router.post("", response_model=PaymentResponse)
async def create_payment(
    payload: PaymentCreateRequest, idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: uuid.UUID):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
async def cancel_payment(payment_id: uuid.UUID):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)
