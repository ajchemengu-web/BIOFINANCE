from decimal import Decimal

from pydantic import BaseModel


class ProviderBalance(BaseModel):
    provider_code: str
    amount: Decimal
    currency: str = "KES"


class BalancesResponse(BaseModel):
    total: Decimal
    currency: str = "KES"
    by_provider: list[ProviderBalance]
