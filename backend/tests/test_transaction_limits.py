"""
Per-transaction amount cap (docs/security-model.md "Fraud protection (MVP
scope)" — "Transaction limits"), Settings.max_transaction_amount. Checked
in both PaymentService.create_payment and create_payment_request.
"""

import uuid

from app.core.config import get_settings


def _register(client) -> str:
    email = f"user-{uuid.uuid4().hex[:8]}@biofinance.dev"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": "Test User"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_merchant(client) -> tuple[str, str]:
    email = f"merchant-{uuid.uuid4().hex[:8]}@biofinance.dev"
    response = client.post(
        "/api/v1/merchants/register",
        json={"business_name": "Java House", "email": email, "password": "password123"},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]

    device_response = client.post(
        "/api/v1/merchant-devices/register",
        json={"device_identifier": "device-1"},
        headers=_auth_headers(token),
    )
    assert device_response.status_code == 200, device_response.text

    profile = client.get("/api/v1/merchants/me", headers=_auth_headers(token))
    return profile.json()["id"], token


def test_customer_payment_over_the_limit_is_rejected(client):
    token = _register(client)
    merchant_id, _ = _create_merchant(client)
    over_limit = get_settings().max_transaction_amount + 1

    response = client.post(
        "/api/v1/payments",
        json={"merchant_id": merchant_id, "amount": str(over_limit), "currency": "KES"},
        headers={**_auth_headers(token), "Idempotency-Key": f"TX-{uuid.uuid4().hex}"},
    )
    assert response.status_code == 400
    assert "maximum" in response.json()["detail"].lower()


def test_customer_payment_at_the_limit_is_allowed_through(client):
    """At the limit, not just under it — this is a "no more than", not a
    strict-less-than boundary."""
    token = _register(client)
    merchant_id, _ = _create_merchant(client)
    at_limit = get_settings().max_transaction_amount

    response = client.post(
        "/api/v1/payments",
        json={"merchant_id": merchant_id, "amount": str(at_limit), "currency": "KES"},
        headers={**_auth_headers(token), "Idempotency-Key": f"TX-{uuid.uuid4().hex}"},
    )
    assert response.status_code == 201, response.text


def test_merchant_payment_request_over_the_limit_is_rejected(client):
    _, merchant_token = _create_merchant(client)
    over_limit = get_settings().max_transaction_amount + 1

    response = client.post(
        "/api/v1/payments/request",
        json={"amount": str(over_limit), "currency": "KES"},
        headers={
            **_auth_headers(merchant_token),
            "Idempotency-Key": f"TX-{uuid.uuid4().hex}",
            "Device-Identifier": "device-1",
        },
    )
    assert response.status_code == 400
