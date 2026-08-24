"""BioID issuance and lookup. DB-backed operations land in Phase 2 (docs/roadmap.md)."""

import secrets
import string

_CODE_ALPHABET = string.ascii_uppercase + string.digits


def generate_bio_id_code() -> str:
    """Generates a display identifier like BF-8X7K29. Never a phone/account/ID number."""
    suffix = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))
    return f"BF-{suffix}"


class BioIDService:
    async def issue(self, user_id):
        raise NotImplementedError("BioIDService.issue — implemented in Phase 2")

    async def get_for_user(self, user_id):
        raise NotImplementedError("BioIDService.get_for_user — implemented in Phase 2")

    async def lock(self, bio_id):
        raise NotImplementedError("BioIDService.lock — implemented in Phase 2")
