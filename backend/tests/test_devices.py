"""
Device registration — the push-token side of BioFinance ID push pairing
(docs/roadmap.md Phase 5). Runs against the real database, like the other
flow tests.
"""

import uuid


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


def test_register_device_creates_a_new_row(client):
    token = _register(client)
    device_identifier = uuid.uuid4().hex

    response = client.post(
        "/api/v1/devices/register",
        json={"device_identifier": device_identifier, "push_token": "fcm-token-1", "platform": "ANDROID"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["device_identifier"] == device_identifier
    assert body["platform"] == "ANDROID"
    assert body["status"] == "ACTIVE"
    assert "push_token" not in body


def test_register_device_upserts_on_same_identifier(client):
    token = _register(client)
    device_identifier = uuid.uuid4().hex

    first = client.post(
        "/api/v1/devices/register",
        json={"device_identifier": device_identifier, "push_token": "fcm-token-old", "platform": "ANDROID"},
        headers=_auth_headers(token),
    )
    assert first.status_code == 200, first.text
    device_id = first.json()["id"]

    second = client.post(
        "/api/v1/devices/register",
        json={"device_identifier": device_identifier, "push_token": "fcm-token-new", "platform": "IOS"},
        headers=_auth_headers(token),
    )
    assert second.status_code == 200, second.text
    body = second.json()
    assert body["id"] == device_id, "re-registering the same device_identifier should update, not duplicate"
    assert body["platform"] == "IOS"


def test_register_device_requires_auth(client):
    response = client.post(
        "/api/v1/devices/register",
        json={"device_identifier": "some-device"},
    )
    assert response.status_code in (401, 403)


def test_register_device_without_push_token_is_allowed(client):
    """A device that hasn't gotten an FCM token yet (denied permission, no
    network) can still register itself — push delivery is best-effort, not
    required (see docs/security-model.md)."""
    token = _register(client)

    response = client.post(
        "/api/v1/devices/register",
        json={"device_identifier": uuid.uuid4().hex},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200, response.text
    assert response.json()["platform"] is None


def test_revoke_device(client):
    token = _register(client)
    register_response = client.post(
        "/api/v1/devices/register",
        json={"device_identifier": uuid.uuid4().hex, "push_token": "fcm-token-1"},
        headers=_auth_headers(token),
    )
    device_id = register_response.json()["id"]

    response = client.delete(f"/api/v1/devices/{device_id}", headers=_auth_headers(token))
    assert response.status_code == 204


def test_revoked_device_is_dropped_from_push_targets(client):
    """The actual point of revocation, not just a status flip — see
    docs/security-model.md ("revoke it ... on ... explicit device
    removal"). Exercised via BioFinance ID push pairing's device_service
    list_push_tokens, the only current consumer."""
    token = _register(client)
    register_response = client.post(
        "/api/v1/devices/register",
        json={"device_identifier": uuid.uuid4().hex, "push_token": "fcm-token-1"},
        headers=_auth_headers(token),
    )
    device_id = register_response.json()["id"]

    client.delete(f"/api/v1/devices/{device_id}", headers=_auth_headers(token))

    import asyncio

    import jwt as pyjwt

    from app.db.database import async_session_factory
    from app.services.device_service import DeviceService

    user_id = uuid.UUID(pyjwt.decode(token, options={"verify_signature": False})["sub"])

    async def _list_tokens():
        async with async_session_factory() as session:
            return await DeviceService(session).list_push_tokens(user_id)

    assert asyncio.run(_list_tokens()) == []


def test_revoke_device_requires_ownership(client):
    token_a = _register(client)
    token_b = _register(client)
    register_response = client.post(
        "/api/v1/devices/register",
        json={"device_identifier": uuid.uuid4().hex},
        headers=_auth_headers(token_a),
    )
    device_id = register_response.json()["id"]

    response = client.delete(f"/api/v1/devices/{device_id}", headers=_auth_headers(token_b))
    assert response.status_code == 404


def test_revoke_nonexistent_device_returns_404(client):
    token = _register(client)
    response = client.delete(f"/api/v1/devices/{uuid.uuid4()}", headers=_auth_headers(token))
    assert response.status_code == 404
