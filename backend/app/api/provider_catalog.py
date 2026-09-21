from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.provider_catalog import ProviderCatalogEntryResponse
from app.services.provider_catalog_service import ProviderCatalogService

router = APIRouter(prefix="/provider-catalog", tags=["provider-catalog"])


@router.get("", response_model=list[ProviderCatalogEntryResponse])
async def list_provider_catalog(country: str | None = None, db: AsyncSession = Depends(get_db)):
    """
    Reference data, not user data — unauthenticated on purpose, same as
    GET /merchants/{id}. This is what a provider-selection screen (mobile/)
    renders after sign-up instead of hardcoding a provider list, and what
    lets a new market or a new partner show up without a client release:
    add a row here (plus a real adapter once there's an integration to
    back it — see app/providers/registry.py), no other code changes.

    ?country=KE filters to that ISO 3166-1 alpha-2 code; omitted, returns
    the whole catalog (including COMING_SOON/DISABLED entries) so a client
    can show "coming soon" rather than just omitting them.
    """
    return await ProviderCatalogService(db).list_entries(country_code=country)
