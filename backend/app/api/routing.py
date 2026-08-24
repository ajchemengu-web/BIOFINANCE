import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.routing_policy import RoutingPolicy
from app.models.user import User
from app.schemas.routing import RoutingPolicyResponse, RoutingPolicyUpdate

router = APIRouter(prefix="/routing-policy", tags=["routing"])


async def _get_or_create(db: AsyncSession, user_id: uuid.UUID) -> RoutingPolicy:
    result = await db.execute(select(RoutingPolicy).where(RoutingPolicy.user_id == user_id))
    policy = result.scalar_one_or_none()
    if policy is None:
        policy = RoutingPolicy(user_id=user_id)
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
    return policy


@router.get("", response_model=RoutingPolicyResponse)
async def get_routing_policy(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _get_or_create(db, user.id)


@router.put("", response_model=RoutingPolicyResponse)
async def update_routing_policy(
    payload: RoutingPolicyUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policy = await _get_or_create(db, user.id)
    policy.mode = payload.mode
    policy.primary_provider_id = payload.primary_provider_id
    policy.fallback_provider_id = payload.fallback_provider_id
    await db.commit()
    await db.refresh(policy)
    return policy
