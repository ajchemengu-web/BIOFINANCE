import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.payments import PaymentCreateRequest, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: PaymentCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        transaction = await PaymentService(db).create_payment(
            user_id=user.id,
            merchant_id=payload.merchant_id,
            amount=payload.amount,
            currency=payload.currency,
            idempotency_key=idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return transaction


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    transaction = await PaymentService(db).get_payment(payment_id)
    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")
    return transaction


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
async def cancel_payment(payment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    transaction = await PaymentService(db).cancel_payment(payment_id)
    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")
    return transaction
