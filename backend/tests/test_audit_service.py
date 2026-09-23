"""
Audit logging (docs/security-model.md "Audit logging") — audit_events has
existed since the first migration but nothing wrote to it until now.
Verifies the documented minimum event set actually lands rows, not just
that the endpoints it's wired into still return the right HTTP status.

Queries the database directly (a fresh AsyncSession per check, not the
TestClient) since there's no read endpoint for audit_events — deliberately
not built this pass, see docs/roadmap.md.
"""

import asyncio
import uuid

from sqlalchemy import select

from app.db.database import async_session_factory
from app.models.audit import AuditEvent


def _events_for(user_id: str, event_type: str) -> list[AuditEvent]:
    async def _query():
        async with async_session_factory() as session:
            result = await session.execute(
                select(AuditEvent).where(
                    AuditEvent.user_id == uuid.UUID(user_id), AuditEvent.event_type == event_type
                )
            )
            return result.scalars().all()

    return asyncio.run(_query())


def _register(client) -> tuple[str, str]:
    """Returns (access_token, email) — see _user_id_from_login for how a
    test recovers the user_id to query audit_events by."""
    email = f"user-{uuid.uuid4().hex[:8]}@biofinance.dev"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": "Test User"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"], email


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _user_id_from_login(client, email: str, password: str = "password123") -> str:
    """BioIDResponse doesn't expose user_id, so decode it off the token
    instead — every access token's `sub` claim is the user's id."""
    import jwt as pyjwt

    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return pyjwt.decode(token, options={"verify_signature": False})["sub"]


def test_login_success_is_audited(client):
    _, email = _register(client)
    user_id = _user_id_from_login(client, email)

    events = _events_for(user_id, "LOGIN_SUCCESS")
    assert len(events) >= 1


def test_login_failure_is_audited_for_a_known_user(client):
    _, email = _register(client)

    response = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-password"})
    assert response.status_code == 401

    user_id = _user_id_from_login(client, email)  # a correct login to recover the user_id
    events = _events_for(user_id, "LOGIN_FAILED")
    assert len(events) >= 1


def test_provider_connect_and_disconnect_are_audited(client):
    token, email = _register(client)
    user_id = _user_id_from_login(client, email)

    connect_response = client.post(
        "/api/v1/providers/connect",
        json={"provider_code": "MPESA", "external_account_ref": uuid.uuid4().hex},
        headers=_auth_headers(token),
    )
    assert connect_response.status_code == 201, connect_response.text
    connection_id = connect_response.json()["id"]

    assert len(_events_for(user_id, "PROVIDER_CONNECTED")) >= 1

    disconnect_response = client.delete(f"/api/v1/providers/{connection_id}", headers=_auth_headers(token))
    assert disconnect_response.status_code == 204

    assert len(_events_for(user_id, "PROVIDER_DISCONNECTED")) >= 1


def test_routing_policy_change_is_audited(client):
    token, email = _register(client)
    user_id = _user_id_from_login(client, email)

    response = client.put(
        "/api/v1/routing-policy",
        json={"mode": "PRIMARY", "primary_provider_id": None},
        headers=_auth_headers(token),
    )
    assert response.status_code == 200, response.text

    assert len(_events_for(user_id, "ROUTING_CHANGED")) >= 1


def test_bioid_lock_is_audited(client):
    token, email = _register(client)
    user_id = _user_id_from_login(client, email)

    response = client.post("/api/v1/bioid/lock", headers=_auth_headers(token))
    assert response.status_code == 200, response.text

    assert len(_events_for(user_id, "BIOID_LOCKED")) >= 1


def test_device_registration_is_audited_once_not_on_every_refresh(client):
    token, email = _register(client)
    user_id = _user_id_from_login(client, email)
    device_identifier = uuid.uuid4().hex

    first = client.post(
        "/api/v1/devices/register",
        json={"device_identifier": device_identifier, "push_token": "token-a"},
        headers=_auth_headers(token),
    )
    assert first.status_code == 200, first.text

    second = client.post(
        "/api/v1/devices/register",
        json={"device_identifier": device_identifier, "push_token": "token-b"},
        headers=_auth_headers(token),
    )
    assert second.status_code == 200, second.text

    events = _events_for(user_id, "DEVICE_REGISTERED")
    assert len(events) == 1, "re-registering the same device shouldn't log a second DEVICE_REGISTERED event"


def test_payment_lifecycle_is_audited(client):
    token, email = _register(client)
    user_id = _user_id_from_login(client, email)

    mpesa_response = client.post(
        "/api/v1/providers/connect",
        json={"provider_code": "MPESA", "external_account_ref": uuid.uuid4().hex},
        headers=_auth_headers(token),
    )
    mpesa_id = mpesa_response.json()["id"]
    client.put(
        "/api/v1/routing-policy",
        json={"mode": "PRIMARY", "primary_provider_id": mpesa_id},
        headers=_auth_headers(token),
    )
    merchant_register_response = client.post(
        "/api/v1/merchants/register",
        json={
            "business_name": "Audit Test Merchant",
            "email": f"merchant-{uuid.uuid4().hex[:8]}@biofinance.dev",
            "password": "password123",
        },
    )
    merchant_token = merchant_register_response.json()["access_token"]
    merchant_profile = client.get("/api/v1/merchants/me", headers=_auth_headers(merchant_token))
    merchant_id = merchant_profile.json()["id"]  # transactions.merchant_id is a real FK — must be a real row

    payment_response = client.post(
        "/api/v1/payments",
        json={"merchant_id": merchant_id, "amount": "1.00", "currency": "KES"},
        headers={**_auth_headers(token), "Idempotency-Key": f"TX-{uuid.uuid4().hex}"},
    )
    assert payment_response.status_code == 201, payment_response.text

    assert len(_events_for(user_id, "PAYMENT_CREATED")) >= 1
    assert len(_events_for(user_id, "PAYMENT_AUTHORIZED")) >= 1

    status = payment_response.json()["status"]
    if status == "COMPLETED":
        assert len(_events_for(user_id, "PAYMENT_COMPLETED")) >= 1
    else:
        assert len(_events_for(user_id, "PAYMENT_FAILED")) >= 1
