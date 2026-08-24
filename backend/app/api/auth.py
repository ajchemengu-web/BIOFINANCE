from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_NOT_IMPLEMENTED = "Implemented in Phase 2 once PostgreSQL is wired up (docs/roadmap.md)"


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)
