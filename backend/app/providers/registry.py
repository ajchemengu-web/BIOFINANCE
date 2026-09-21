"""
Maps a ProviderConnection.provider_code to a PaymentProvider instance —
the technical counterpart to app/models/provider_catalog.py, which is the
business/product truth of which codes exist and are connectable. This
module answers a narrower question: given a code the catalog already
vouched for (POST /providers/connect checks it, and the database's own
foreign key backs that up), how do we actually talk to it?

MPESA resolves to the real DarajaProvider once Daraja credentials are
configured (Settings.daraja_configured); until then, and for every other
catalog code, it falls back to a mock — a bespoke one for the three
providers this app started with (so their existing default balances/tests
keep working), a generic one for anything else. That generic fallback is
what lets a brand-new catalog entry work end-to-end — connect, route,
pay — the moment it's added, no code change required, before a real
integration agreement is in place. Adding the *real* integration later is
still a new adapter class here, same as DarajaProvider was for MPESA.
"""

from app.core.config import get_settings
from app.providers.base import PaymentProvider
from app.providers.daraja import DarajaProvider
from app.providers.mock_airtel import MockAirtelProvider
from app.providers.mock_bank import MockBankProvider
from app.providers.mock_generic import GenericMockProvider
from app.providers.mock_mpesa import MockMpesaProvider

_legacy_mock_providers: dict[str, PaymentProvider] = {
    "MPESA": MockMpesaProvider(),
    "EQUITY": MockBankProvider(),
    "AIRTEL": MockAirtelProvider(),
}

_generic_mock_providers: dict[str, PaymentProvider] = {}

_daraja_provider: DarajaProvider | None = None


def get_provider(provider_code: str) -> PaymentProvider:
    if provider_code == "MPESA":
        settings = get_settings()
        if settings.daraja_configured:
            global _daraja_provider
            if _daraja_provider is None:
                _daraja_provider = DarajaProvider(settings)
            return _daraja_provider
        return _legacy_mock_providers["MPESA"]

    if provider_code in _legacy_mock_providers:
        return _legacy_mock_providers[provider_code]

    # Cached per code so an account's mock balance persists across calls
    # within this process, same guarantee the legacy mocks give.
    if provider_code not in _generic_mock_providers:
        _generic_mock_providers[provider_code] = GenericMockProvider(provider_code)
    return _generic_mock_providers[provider_code]
