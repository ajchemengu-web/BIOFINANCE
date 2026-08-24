"""
Safaricom Daraja 3.0 adapter — implements PaymentProvider against the Daraja
sandbox (docs: https://developer.safaricom.co.ke). Credentials come from
Settings only, never hardcoded (docs/security-model.md).

NOT YET LIVE-TESTED — the account requesting this feature had no Daraja
sandbox credentials to test against, so this is written strictly to the
published API contract and covered by unit tests against a mocked HTTP
transport (tests/test_daraja_provider.py), not a real sandbox call. Treat
the request/response shapes as "should be right per the docs", not
"confirmed working", until it's run against real credentials.

Architecture note: STK push is asynchronous by nature — initiate_payment
only confirms the prompt reached the phone (status=PENDING); the actual
outcome arrives later via the callback webhook
(app/api/providers.py:daraja_callback) or a get_payment_status poll.
BioRouter's fallback loop (app/services/router_service.py) currently only
treats a PENDING result as "not SUCCESS" and stops there rather than
falling back — reconciling BioRouter with Daraja's async model (leaving
the transaction in AUTHORIZATION_PENDING until the callback lands, instead
of resolving synchronously like the mock providers do) is unfinished work,
not something this file can fix on its own.
"""

import base64
import uuid
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

import httpx

from app.core.config import Settings
from app.providers.base import BalanceResult, PaymentProvider, PaymentRequest, PaymentResult

_SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"
_PRODUCTION_BASE_URL = "https://api.safaricom.co.ke"

# Safaricom STK push result codes (subset) — see Daraja API docs.
_RESULT_CODE_STATUS = {
    0: "SUCCESS",
    1032: "DECLINED",  # request cancelled by user
    1037: "TIMEOUT",  # user didn't respond to the prompt in time
    1: "DECLINED",  # insufficient funds
}


class DarajaProvider(PaymentProvider):
    code = "MPESA"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = (
            _SANDBOX_BASE_URL if settings.daraja_environment == "sandbox" else _PRODUCTION_BASE_URL
        )

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

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def _password(self, timestamp: str) -> str:
        raw = f"{self._settings.daraja_shortcode}{self._settings.daraja_passkey}{timestamp}"
        return base64.b64encode(raw.encode()).decode()

    def _callback_url(self) -> str:
        base = self._settings.daraja_callback_base_url.rstrip("/")
        return f"{base}/api/v1/providers/daraja/callback"

    async def get_balance(self, account_id: str) -> BalanceResult:
        # Daraja has no "check a customer's M-PESA balance" endpoint — only
        # the shortcode's own account balance (a separate B2C-style query),
        # which isn't the same thing as a customer's wallet balance. There's
        # no equivalent to expose here; BioWallet can't show a real M-PESA
        # balance once this replaces the mock, only transaction outcomes.
        raise NotImplementedError(
            "Daraja has no customer-balance API — get_balance isn't meaningful for this provider"
        )

    async def initiate_payment(self, request: PaymentRequest) -> PaymentResult:
        if not self._settings.daraja_callback_base_url:
            raise ValueError("DARAJA_CALLBACK_BASE_URL is not configured — Safaricom needs a public HTTPS URL")

        timestamp = self._timestamp()
        # Amount must be a whole number of shillings for Daraja.
        amount = int(request.amount.to_integral_value(rounding=ROUND_HALF_UP))
        # account_id is the customer's phone number for this provider (MSISDN,
        # e.g. 2547XXXXXXXX) — a different convention from the mock providers,
        # where it's an opaque account reference.
        phone_number = request.account_id

        access_token = await self._get_access_token()
        payload = {
            "BusinessShortCode": self._settings.daraja_shortcode,
            "Password": self._password(timestamp),
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": self._settings.daraja_shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self._callback_url(),
            "AccountReference": request.reference[:12],  # Daraja caps this at 12 chars
            "TransactionDesc": "BioFinance payment",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/mpesa/stkpush/v1/processrequest",
                headers={"Authorization": f"Bearer {access_token}"},
                json=payload,
            )
            body = response.json()

        if body.get("ResponseCode") == "0":
            return PaymentResult(
                provider_reference=body["CheckoutRequestID"], status="PENDING", raw=body
            )
        return PaymentResult(
            provider_reference=body.get("MerchantRequestID", str(uuid.uuid4())),
            status="ERROR",
            raw=body,
        )

    async def get_payment_status(self, transaction_id: str) -> PaymentResult:
        """`transaction_id` here is the CheckoutRequestID returned by initiate_payment."""
        timestamp = self._timestamp()
        access_token = await self._get_access_token()
        payload = {
            "BusinessShortCode": self._settings.daraja_shortcode,
            "Password": self._password(timestamp),
            "Timestamp": timestamp,
            "CheckoutRequestID": transaction_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/mpesa/stkpushquery/v1/query",
                headers={"Authorization": f"Bearer {access_token}"},
                json=payload,
            )
            body = response.json()

        # "Transaction is being processed" — the customer hasn't responded
        # to the prompt yet, not a final outcome.
        if body.get("errorCode") == "500.001.1001":
            return PaymentResult(provider_reference=transaction_id, status="PENDING", raw=body)

        result_code = body.get("ResultCode")
        if result_code is None:
            return PaymentResult(provider_reference=transaction_id, status="ERROR", raw=body)
        status = _RESULT_CODE_STATUS.get(int(result_code), "DECLINED")
        return PaymentResult(provider_reference=transaction_id, status=status, raw=body)

    async def refund_payment(self, transaction_id: str) -> PaymentResult:
        # Daraja's reversal endpoint (/mpesa/reversal/v1/request) needs a
        # SecurityCredential — the initiator password encrypted with
        # Safaricom's public certificate (a .cer file from the developer
        # portal), plus an initiator name. That's a separate credential this
        # app doesn't collect anywhere yet (see docs/security-model.md), so
        # implementing the call itself without being able to test the
        # encryption step against it would be guessing. Left unimplemented
        # rather than shipping something unverifiable.
        raise NotImplementedError(
            "DarajaProvider.refund_payment — needs SecurityCredential setup, not yet implemented"
        )
