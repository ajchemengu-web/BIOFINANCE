from fastapi import APIRouter, HTTPException, status

from app.schemas.balances import BalancesResponse

router = APIRouter(prefix="/balances", tags=["balances"])

_NOT_IMPLEMENTED = "Implemented in Phase 2 once PostgreSQL is wired up (docs/roadmap.md)"


@router.get("", response_model=BalancesResponse)
async def get_balances():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)
