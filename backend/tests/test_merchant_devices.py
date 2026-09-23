"""
POST /merchant-devices/register — the device-registration side of
merchant_devices enforcement (docs/roadmap.md Phase 5, "Merchant-side
integrity"). Mirrors tests/test_devices.py's shape for the customer-side
devices table.
"""

import uuid


def _register_merchant(client) -> str:
    email = f"merchant-{uuid.uuid4().hex[:8]}@biofinance.dev"
    response = client.post(
        "/api/v1/merchants/register",
        json={"business_name": "Naivas", "email": email, "password": "password123"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_register_device_creates_a_new_row(client):
    token = _register_merchant(client)
    device_identifier = uuid.uuid4().hex

    response = client.post(
        "/api/v1/merchant-devices/register",
        json={"device_identifier": device_identifier},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["device_identifier"] == device_identifier
    assert body["status"] == "ACTIVE"


def test_register_device_upserts_on_same_identifier(client):
    token = _register_merchant(client)
    device_identifier = uuid.uuid4().hex

    first = client.post(
        "/api/v1/merchant-devices/register",
        json={"device_identifier": device_identifier},
        headers=_auth_headers(token),
    )
    assert first.status_code == 200, first.text

    second = client.post(
        "/api/v1/merchant-devices/register",
        json={"device_identifier": device_identifier},
        headers=_auth_headers(token),
    )
    assert second.status_code == 200, second.text
    assert second.json()["id"] == first.json()["id"], "re-registering the same device_identifier should update, not duplicate"


def test_register_device_requires_merchant_auth(client):
    response = client.post(
        "/api/v1/merchant-devices/register",
        json={"device_identifier": "some-device"},
    )
    assert response.status_code in (401, 403)


def test_register_device_rejects_a_customer_token(client):
    """A customer's own token must be structurally rejected here — not
    just "wrong merchant", a completely different token type."""
    email = f"user-{uuid.uuid4().hex[:8]}@biofinance.dev"
    customer_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": "Test User"},
    )
    customer_token = customer_response.json()["access_token"]

    response = client.post(
        "/api/v1/merchant-devices/register",
        json={"device_identifier": "some-device"},
        headers=_auth_headers(customer_token),
    )
    assert response.status_code == 401


def test_revoked_device_fails_require_registered(client):
    """The actual point of revocation: a revoked terminal must no longer
    pass POST /payments/request's device check, even with a valid
    merchant token — exercised via MerchantDeviceService.require_registered
    directly since that's the only current consumer."""
    token = _register_merchant(client)
    device_identifier = uuid.uuid4().hex
    register_response = client.post(
        "/api/v1/merchant-devices/register",
        json={"device_identifier": device_identifier},
        headers=_auth_headers(token),
    )
    device_id = register_response.json()["id"]

    revoke_response = client.delete(f"/api/v1/merchant-devices/{device_id}", headers=_auth_headers(token))
    assert revoke_response.status_code == 204

    import asyncio

    import jwt as pyjwt
    import pytest

    from app.db.database import async_session_factory
    from app.services.merchant_device_service import MerchantDeviceService

    merchant_id = uuid.UUID(pyjwt.decode(token, options={"verify_signature": False})["sub"])

    async def _check():
        async with async_session_factory() as session:
            await MerchantDeviceService(session).require_registered(merchant_id, device_identifier)

    with pytest.raises(PermissionError):
        asyncio.run(_check())


def test_revoke_device_requires_ownership(client):
    token_a = _register_merchant(client)
    token_b = _register_merchant(client)
    register_response = client.post(
        "/api/v1/merchant-devices/register",
        json={"device_identifier": uuid.uuid4().hex},
        headers=_auth_headers(token_a),
    )
    device_id = register_response.json()["id"]

    response = client.delete(f"/api/v1/merchant-devices/{device_id}", headers=_auth_headers(token_b))
    assert response.status_code == 404


def test_revoke_nonexistent_device_returns_404(client):
    token = _register_merchant(client)
    response = client.delete(f"/api/v1/merchant-devices/{uuid.uuid4()}", headers=_auth_headers(token))
    assert response.status_code == 404
