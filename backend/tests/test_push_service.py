"""
PushService tests against a mocked HTTP transport (respx) — no real
Firebase project/service-account credentials required or contacted. These
confirm the OAuth2 service-account (JWT-bearer) exchange and the FCM HTTP
v1 send both follow the published API contracts; they cannot confirm a
real Firebase project actually accepts these requests (see the docstring
in app/services/push_service.py).
"""

import json
from decimal import Decimal

import pytest
import respx
from httpx import Response

from app.core.config import Settings
from app.services.push_service import PushService
from tests.conftest import fake_fcm_service_account_json

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_SEND_URL = "https://fcm.googleapis.com/v1/projects/test-project/messages:send"

_TEST_SETTINGS = Settings(fcm_project_id="test-project", fcm_service_account_json=fake_fcm_service_account_json())


def _mock_oauth():
    respx.post(_TOKEN_URL).mock(return_value=Response(200, json={"access_token": "fake-token", "expires_in": 3599}))


@pytest.mark.asyncio
@respx.mock
async def test_send_payment_approval_request_succeeds():
    _mock_oauth()
    send_route = respx.post(_SEND_URL).mock(return_value=Response(200, json={"name": "projects/test-project/messages/1"}))

    service = PushService(_TEST_SETTINGS)
    result = await service.send_payment_approval_request(
        push_token="device-token-1",
        transaction_id="tx-1",
        merchant_name="Java House",
        amount=Decimal("450.00"),
        currency="KES",
    )

    assert result is True
    sent_body = json.loads(send_route.calls.last.request.content)
    assert sent_body["message"]["token"] == "device-token-1"
    assert sent_body["message"]["data"]["transaction_id"] == "tx-1"
    assert "Java House" in sent_body["message"]["notification"]["body"]


@pytest.mark.asyncio
@respx.mock
async def test_send_payment_approval_request_returns_false_on_stale_token():
    """FCM tokens go stale routinely (docs/security-model.md, "Delivery
    isn't guaranteed") — a rejection from Google must not raise."""
    _mock_oauth()
    respx.post(_SEND_URL).mock(
        return_value=Response(404, json={"error": {"status": "NOT_FOUND", "message": "Requested entity was not found."}})
    )

    service = PushService(_TEST_SETTINGS)
    result = await service.send_payment_approval_request(
        push_token="stale-token",
        transaction_id="tx-2",
        merchant_name="Java House",
        amount=Decimal("450.00"),
        currency="KES",
    )

    assert result is False


@pytest.mark.asyncio
async def test_send_payment_approval_request_is_a_noop_when_not_configured():
    unconfigured = Settings(fcm_project_id="", fcm_service_account_json="")
    service = PushService(unconfigured)

    result = await service.send_payment_approval_request(
        push_token="device-token-1",
        transaction_id="tx-3",
        merchant_name="Java House",
        amount=Decimal("450.00"),
        currency="KES",
    )

    assert result is False
