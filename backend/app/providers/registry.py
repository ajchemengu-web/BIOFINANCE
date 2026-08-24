"""
Maps a ProviderConnection.provider_code to a PaymentProvider instance.
Swapping MPESA from MockMpesaProvider to DarajaProvider in Phase 4 is a
one-line change here — nothing else in the codebase needs to know.
"""

from app.providers.base import PaymentProvider
from app.providers.mock_airtel import MockAirtelProvider
from app.providers.mock_bank import MockBankProvider
from app.providers.mock_mpesa import MockMpesaProvider

_PROVIDERS: dict[str, PaymentProvider] = {
    "MPESA": MockMpesaProvider(),
    "EQUITY": MockBankProvider(),
    "AIRTEL": MockAirtelProvider(),
}


def get_provider(provider_code: str) -> PaymentProvider:
    try:
        return _PROVIDERS[provider_code]
    except KeyError as exc:
        raise ValueError(f"Unknown provider_code: {provider_code}") from exc
