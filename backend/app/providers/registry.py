"""
Maps a ProviderConnection.provider_code to a PaymentProvider instance.
MPESA resolves to the real DarajaProvider once Daraja credentials are
configured (Settings.daraja_configured); until then it falls back to the
in-memory mock so the rest of the app keeps working without them.
"""

from app.core.config import get_settings
from app.providers.base import PaymentProvider
from app.providers.daraja import DarajaProvider
from app.providers.mock_airtel import MockAirtelProvider
from app.providers.mock_bank import MockBankProvider
from app.providers.mock_mpesa import MockMpesaProvider

_mock_providers: dict[str, PaymentProvider] = {
    "MPESA": MockMpesaProvider(),
    "EQUITY": MockBankProvider(),
    "AIRTEL": MockAirtelProvider(),
}

_daraja_provider: DarajaProvider | None = None


def get_provider(provider_code: str) -> PaymentProvider:
    if provider_code == "MPESA":
        settings = get_settings()
        if settings.daraja_configured:
            global _daraja_provider
            if _daraja_provider is None:
                _daraja_provider = DarajaProvider(settings)
            return _daraja_provider
        return _mock_providers["MPESA"]

    try:
        return _mock_providers[provider_code]
    except KeyError as exc:
        raise ValueError(f"Unknown provider_code: {provider_code}") from exc
