"""
DarajaProvider tests against a mocked HTTP transport (respx) — no real
Safaricom sandbox credentials required or contacted. These confirm the
request/response handling matches the published Daraja API contract; they
cannot confirm the sandbox actually accepts these requests (see the
docstring in app/providers/daraja.py).
"""

from decimal import Decimal

import pytest
import respx
from httpx import Response

from app.core.config import Settings
from app.providers.base import PaymentRequest
from app.providers.daraja import DarajaProvider

_TEST_SETTINGS = Settings(
    daraja_consumer_key="test-key",
    daraja_consumer_secret="test-secret",
    daraja_shortcode="174379",
    daraja_passkey="test-passkey",
    daraja_environment="sandbox",
    daraja_callback_base_url="https://example.ngrok.io",
)

_SANDBOX = "https://sandbox.safaricom.co.ke"


def _mock_oauth():
    respx.get(f"{_SANDBOX}/oauth/v1/generate").mock(
        return_value=Response(200, json={"access_token": "fake-token", "expires_in": "3599"})
    )


@pytest.mark.asyncio
@respx.mock
async def test_initiate_payment_returns_pending_on_accepted_request():
    _mock_oauth()
    respx.post(f"{_SANDBOX}/mpesa/stkpush/v1/processrequest").mock(
        return_value=Response(
            200,
            json={
                "MerchantRequestID": "merchant-1",
                "CheckoutRequestID": "checkout-1",
                "ResponseCode": "0",
                "ResponseDescription": "Success. Request accepted for processing",
                "CustomerMessage": "Success. Request accepted for processing",
            },
        )
    )

    provider = DarajaProvider(_TEST_SETTINGS)
    result = await provider.initiate_payment(
        PaymentRequest(account_id="254708374149", amount=Decimal("450.00"), currency="KES", reference="TX-1")
    )

    assert result.status == "PENDING"
    assert result.provider_reference == "checkout-1"


@pytest.mark.asyncio
@respx.mock
async def test_initiate_payment_returns_error_when_rejected():
    _mock_oauth()
    respx.post(f"{_SANDBOX}/mpesa/stkpush/v1/processrequest").mock(
        return_value=Response(
            200,
            json={
                "MerchantRequestID": "merchant-2",
                "ResponseCode": "1",
                "ResponseDescription": "Unable to lock subscriber",
            },
        )
    )

    provider = DarajaProvider(_TEST_SETTINGS)
    result = await provider.initiate_payment(
        PaymentRequest(account_id="254708374149", amount=Decimal("450.00"), currency="KES", reference="TX-2")
    )

    assert result.status == "ERROR"


@pytest.mark.asyncio
async def test_initiate_payment_requires_callback_url():
    settings_without_callback = _TEST_SETTINGS.model_copy(update={"daraja_callback_base_url": ""})
    provider = DarajaProvider(settings_without_callback)

    with pytest.raises(ValueError, match="DARAJA_CALLBACK_BASE_URL"):
        await provider.initiate_payment(
            PaymentRequest(account_id="254708374149", amount=Decimal("450.00"), currency="KES", reference="TX-3")
        )


@pytest.mark.asyncio
@respx.mock
async def test_get_payment_status_maps_success():
    _mock_oauth()
    respx.post(f"{_SANDBOX}/mpesa/stkpushquery/v1/query").mock(
        return_value=Response(200, json={"ResultCode": 0, "ResultDesc": "The service request is processed successfully."})
    )

    provider = DarajaProvider(_TEST_SETTINGS)
    result = await provider.get_payment_status("checkout-1")

    assert result.status == "SUCCESS"


@pytest.mark.asyncio
@respx.mock
async def test_get_payment_status_maps_cancelled():
    _mock_oauth()
    respx.post(f"{_SANDBOX}/mpesa/stkpushquery/v1/query").mock(
        return_value=Response(200, json={"ResultCode": 1032, "ResultDesc": "Request cancelled by user"})
    )

    provider = DarajaProvider(_TEST_SETTINGS)
    result = await provider.get_payment_status("checkout-1")

    assert result.status == "DECLINED"


@pytest.mark.asyncio
@respx.mock
async def test_get_payment_status_still_processing():
    _mock_oauth()
    respx.post(f"{_SANDBOX}/mpesa/stkpushquery/v1/query").mock(
        return_value=Response(
            500,
            json={
                "requestId": "req-1",
                "errorCode": "500.001.1001",
                "errorMessage": "The transaction is being processed",
            },
        )
    )

    provider = DarajaProvider(_TEST_SETTINGS)
    result = await provider.get_payment_status("checkout-1")

    assert result.status == "PENDING"


@pytest.mark.asyncio
async def test_get_balance_not_implemented():
    provider = DarajaProvider(_TEST_SETTINGS)
    with pytest.raises(NotImplementedError):
        await provider.get_balance("254708374149")


@pytest.mark.asyncio
async def test_refund_not_implemented():
    provider = DarajaProvider(_TEST_SETTINGS)
    with pytest.raises(NotImplementedError):
        await provider.refund_payment("checkout-1")
