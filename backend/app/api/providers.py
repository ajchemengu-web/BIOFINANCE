import uuid

from fastapi import APIRouter, HTTPException, status

from app.schemas.providers import ProviderConnectionResponse, ProviderConnectRequest

router = APIRouter(prefix="/providers", tags=["providers"])

_NOT_IMPLEMENTED = "Implemented in Phase 2 once PostgreSQL is wired up (docs/roadmap.md)"


@router.get("", response_model=list[ProviderConnectionResponse])
async def list_providers():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.post("/connect", response_model=ProviderConnectionResponse)
async def connect_provider(payload: ProviderConnectRequest):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.delete("/{provider_id}")
async def disconnect_provider(provider_id: uuid.UUID):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.post("/daraja/callback")
async def daraja_callback():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Implemented in Phase 4 (Daraja sandbox)")
