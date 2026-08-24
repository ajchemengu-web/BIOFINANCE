import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.payments import PaymentCreateRequest, PaymentRequestCreate, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: PaymentCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Customer-initiated (mobile/) — the caller has already authenticated,
    so this routes and resolves immediately."""
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


@router.post("/request", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_request(
    payload: PaymentRequestCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
):
    """
    Merchant-initiated (biopos/) — no customer session here (BioPOS has no
    customer auth), so this just opens a request awaiting a customer to
    claim it via POST /payments/{id}/claim. Unauthenticated for the same
    reason POST /merchants is: there's no merchant-auth endpoint yet
    (docs/roadmap.md Phase 5).
    """
    transaction = await PaymentService(db).create_payment_request(
        merchant_id=payload.merchant_id,
        amount=payload.amount,
        currency=payload.currency,
        idempotency_key=idempotency_key,
    )
    return transaction


@router.post("/{payment_id}/claim", response_model=PaymentResponse)
async def claim_payment_request(
    payment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    A customer, authenticated in their own session, fulfills a merchant's
    payment request — attaches their BioID and routes it through
    BioRouter exactly like create_payment does.
    """
    try:
        transaction = await PaymentService(db).claim_payment_request(payment_id, user.id)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
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
