"""The provider catalog — see app/models/provider_catalog.py for why this
is a separate source of truth from app/providers/registry.py."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider_catalog import ProviderCatalogEntry


class ProviderCatalogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_entries(self, country_code: str | None = None) -> list[ProviderCatalogEntry]:
        query = select(ProviderCatalogEntry)
        if country_code is not None:
            query = query.where(ProviderCatalogEntry.country_code == country_code.upper())
        result = await self.db.execute(query.order_by(ProviderCatalogEntry.display_name))
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> ProviderCatalogEntry | None:
        return await self.db.get(ProviderCatalogEntry, code)
