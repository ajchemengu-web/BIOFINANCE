"""
Safaricom Daraja 3.0 adapter. Implements the PaymentProvider interface against the
Daraja sandbox (docs: https://developer.safaricom.co.ke). Only OAuth token
acquisition is implemented in Phase 0 — STK push, status query, and refund are
stubbed pending Phase 4 (docs/roadmap.md). Credentials come from Settings only,
never hardcoded (docs/security-model.md).
"""

import base64

import httpx

from app.core.config import Settings
from app.providers.base import BalanceResult, PaymentProvider, PaymentRequest, PaymentResult

_SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"


class DarajaProvider(PaymentProvider):
    code = "MPESA"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = _SANDBOX_BASE_URL if settings.daraja_environment == "sandbox" else ""

    async def _get_access_token(self) -> str:
        credentials = f"{self._settings.daraja_consumer_key}:{self._settings.daraja_consumer_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/oauth/v1/generate?grant_type=client_credentials",
                headers={"Authorization": f"Basic {encoded}"},
            )
            response.raise_for_status()
            return response.json()["access_token"]

    async def get_balance(self, account_id: str) -> BalanceResult:
        raise NotImplementedError("DarajaProvider.get_balance — implemented in Phase 4")

    async def initiate_payment(self, request: PaymentRequest) -> PaymentResult:
        # Phase 4: STK push via /mpesa/stkpush/v1/processrequest, amount as int (Decimal → int shillings)
        raise NotImplementedError("DarajaProvider.initiate_payment — implemented in Phase 4")

    async def get_payment_status(self, transaction_id: str) -> PaymentResult:
        raise NotImplementedError("DarajaProvider.get_payment_status — implemented in Phase 4")

    async def refund_payment(self, transaction_id: str) -> PaymentResult:
        raise NotImplementedError("DarajaProvider.refund_payment — implemented in Phase 4")
