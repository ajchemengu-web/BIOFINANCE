import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_merchant, get_current_user
from app.core.rate_limit import RateLimitExceeded
from app.db.database import get_db
from app.models.merchant import Merchant
from app.models.user import User
from app.schemas.payments import PaymentCreateRequest, PaymentRequestCreate, PaymentResponse
from app.services.merchant_device_service import MerchantDeviceService
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
    device_identifier: str = Header(..., alias="Device-Identifier"),
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    """
    Merchant-initiated (biopos/), authenticated as the merchant (docs/
    roadmap.md Phase 5, "Real merchant authentication") — this opens a
    request against the calling merchant's own id, never a client-supplied
    one, then awaits a customer to claim it via POST /payments/{id}/claim.

    Device-Identifier must be one this merchant has registered via
    POST /merchant-devices/register (§33 of the source PRD,
    docs/security-model.md "Merchant-side integrity") — the merchant token
    alone proves *which merchant*, this proves *which terminal*, so a
    leaked/shared credential can't be used from an arbitrary device.

    payload.bio_id_code is optional — the merchant reading a customer's
    BioFinance ID off them at the till (BioFinance ID push pairing) rather
    than opening a blind request. See PaymentService.create_payment_request.
    """
    try:
        await MerchantDeviceService(db).require_registered(merchant.id, device_identifier)
        transaction = await PaymentService(db).create_payment_request(
            merchant_id=merchant.id,
            amount=payload.amount,
            currency=payload.currency,
            idempotency_key=idempotency_key,
            bio_id_code=payload.bio_id_code,
        )
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except RateLimitExceeded as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(exc)) from exc
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
    BioRouter exactly like create_payment does. If the request was opened
    with a target BioFinance ID (push pairing), only that customer's
    session may claim it — anyone else gets 403.
    """
    try:
        transaction = await PaymentService(db).claim_payment_request(payment_id, user.id)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return transaction


@router.get("/pending", response_model=list[PaymentResponse])
async def list_pending_payments(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Fallback discovery for BioFinance ID push pairing when the push never
    arrives (docs/security-model.md) — every targeted request awaiting
    this user specifically. Must be registered ahead of GET /{payment_id}
    below, or FastAPI tries to parse "pending" as a payment_id and 422s.
    """
    return await PaymentService(db).list_pending_for_user(user.id)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    transaction = await PaymentService(db).get_payment(payment_id)
    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")
    return transaction


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
async def cancel_payment(
    payment_id: uuid.UUID,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    """
    Merchant-only, and only the merchant that owns the request — cancel is
    exclusively a BioPOS operation (docs/roadmap.md Phase 5; mobile/ never
    calls this), so the same authentication this route needed for creation
    applies here too.
    """
    try:
        transaction = await PaymentService(db).cancel_payment(payment_id, merchant.id)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")
    return transaction
