"""BioID issuance and lookup."""

import secrets
import string
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bioid import BioID

_CODE_ALPHABET = string.ascii_uppercase + string.digits


def generate_bio_id_code() -> str:
    """Generates a display identifier like BF-8X7K29. Never a phone/account/ID number."""
    suffix = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))
    return f"BF-{suffix}"


class BioIDService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def issue(self, user_id: uuid.UUID) -> BioID:
        bio_id = BioID(user_id=user_id, code=generate_bio_id_code())
        self.db.add(bio_id)
        await self.db.commit()
        await self.db.refresh(bio_id)
        return bio_id

    async def get_for_user(self, user_id: uuid.UUID) -> BioID | None:
        result = await self.db.execute(select(BioID).where(BioID.user_id == user_id))
        return result.scalar_one_or_none()

    async def lock(self, bio_id: BioID) -> BioID:
        bio_id.status = "LOCKED"
        await self.db.commit()
        await self.db.refresh(bio_id)
        return bio_id
