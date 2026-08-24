from fastapi import APIRouter, HTTPException, status

from app.schemas.bioid import BioIDResponse

router = APIRouter(prefix="/bioid", tags=["bioid"])

_NOT_IMPLEMENTED = "Implemented in Phase 2 once PostgreSQL is wired up (docs/roadmap.md)"


@router.post("", response_model=BioIDResponse)
async def issue_bioid():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.get("", response_model=BioIDResponse)
async def get_bioid():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.post("/lock")
async def lock_bioid():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)
