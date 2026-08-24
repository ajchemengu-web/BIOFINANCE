from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.bioid import BioIDResponse
from app.services.bioid_service import BioIDService

router = APIRouter(prefix="/bioid", tags=["bioid"])


@router.post("", response_model=BioIDResponse, status_code=status.HTTP_201_CREATED)
async def issue_bioid(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = BioIDService(db)
    existing = await service.get_for_user(user.id)
    if existing is not None:
        return existing
    return await service.issue(user.id)


@router.get("", response_model=BioIDResponse)
async def get_bioid(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bio_id = await BioIDService(db).get_for_user(user.id)
    if bio_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No BioID issued for this user")
    return bio_id


@router.post("/lock", response_model=BioIDResponse)
async def lock_bioid(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = BioIDService(db)
    bio_id = await service.get_for_user(user.id)
    if bio_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No BioID issued for this user")
    return await service.lock(bio_id)
