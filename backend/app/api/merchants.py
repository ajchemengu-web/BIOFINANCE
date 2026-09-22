import secrets
import string
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_merchant
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.db.database import get_db
from app.models.merchant import Merchant
from app.schemas.auth import TokenResponse
from app.schemas.merchants import MerchantLoginRequest, MerchantRegisterRequest, MerchantResponse

router = APIRouter(prefix="/merchants", tags=["merchants"])


def _generate_merchant_code() -> str:
    return "MC-" + "".join(secrets.choice(string.digits) for _ in range(6))


def _merchant_tokens(merchant_id: uuid.UUID) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(str(merchant_id), token_type="merchant_access"),
        refresh_token=create_refresh_token(str(merchant_id), token_type="merchant_refresh"),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_merchant(payload: MerchantRegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Replaces the old unauthenticated POST /merchants (docs/roadmap.md
    Phase 5, "Real merchant authentication") — a merchant now has real
    credentials distinct from the customer users table, and BioPOS's
    "sign in" no longer means "create a fresh row every time".
    """
    existing = await db.execute(select(Merchant).where(Merchant.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    merchant = Merchant(
        business_name=payload.business_name,
        merchant_code=_generate_merchant_code(),
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)

    return _merchant_tokens(merchant.id)


@router.post("/login", response_model=TokenResponse)
async def login_merchant(payload: MerchantLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Merchant).where(Merchant.email == payload.email))
    merchant = result.scalar_one_or_none()
    if merchant is None or merchant.password_hash is None or not verify_password(
        payload.password, merchant.password_hash
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    return _merchant_tokens(merchant.id)


@router.get("/me", response_model=MerchantResponse)
async def get_current_merchant_profile(merchant: Merchant = Depends(get_current_merchant)):
    return merchant


@router.get("/{merchant_id}", response_model=MerchantResponse)
async def get_merchant(merchant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Unauthenticated on purpose — a receipt or a payment-request response
    needs to show whose request it is (business_name) without requiring
    the viewer to be that merchant. Nothing here is sensitive: no email,
    no password_hash, just what MerchantResponse already exposed before
    this endpoint required any auth.
    """
    merchant = await db.get(Merchant, merchant_id)
    if merchant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Merchant not found")
    return merchant
