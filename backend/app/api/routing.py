from fastapi import APIRouter, HTTPException, status

from app.schemas.routing import RoutingPolicyResponse, RoutingPolicyUpdate

router = APIRouter(prefix="/routing-policy", tags=["routing"])

_NOT_IMPLEMENTED = "Implemented in Phase 2 once PostgreSQL is wired up (docs/roadmap.md)"


@router.get("", response_model=RoutingPolicyResponse)
async def get_routing_policy():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.put("", response_model=RoutingPolicyResponse)
async def update_routing_policy(payload: RoutingPolicyUpdate):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)
