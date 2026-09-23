from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.audit import AuditEventResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-events", tags=["audit"])


@router.get("", response_model=list[AuditEventResponse])
async def list_my_audit_events(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    A user's own activity/security log — logins, device changes, provider
    connections, routing changes, their payment lifecycle, BioID locks.
    Scoped strictly to the caller's own user_id; there is no admin/role
    concept anywhere in this app, and this endpoint doesn't invent one —
    it can only ever answer "what happened on my account", never anyone
    else's (see docs/roadmap.md for what a broader admin/ops view would
    still need).
    """
    return await AuditService(db).list_for_user(user.id, limit=limit)
