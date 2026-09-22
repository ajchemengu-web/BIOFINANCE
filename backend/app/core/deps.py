import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.database import get_db
from app.models.merchant import Merchant
from app.models.user import User

_bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


async def get_current_merchant(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Merchant:
    """
    Distinct token type ("merchant_access", not "access") from
    get_current_user above — a customer's token is structurally rejected
    here and a merchant's token is structurally rejected by get_current_user,
    not just by which endpoint happens to call which dependency. See
    docs/security-model.md "Merchant-side integrity".
    """
    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc

    if payload.get("type") != "merchant_access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")

    merchant = await db.get(Merchant, uuid.UUID(payload["sub"]))
    if merchant is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Merchant not found")
    return merchant
