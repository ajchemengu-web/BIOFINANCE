"""
Provider catalog — the DB-backed source of truth for which financial
providers exist and can be connected (docs/architecture.md "Provider
catalog"). Runs against the real database, seeded by migration 0004 with
MPESA/EQUITY/AIRTEL as AVAILABLE, Kenya/KES entries.
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


def test_catalog_list_is_public_and_includes_seeded_providers(client):
    response = client.get("/api/v1/provider-catalog")
    assert response.status_code == 200, response.text
    codes = {entry["code"] for entry in response.json()}
    assert {"MPESA", "EQUITY", "AIRTEL"} <= codes


def test_catalog_filters_by_country(client):
    response = client.get("/api/v1/provider-catalog", params={"country": "KE"})
    assert response.status_code == 200, response.text
    assert all(entry["country_code"] == "KE" for entry in response.json())

    empty = client.get("/api/v1/provider-catalog", params={"country": "ZZ"})
    assert empty.status_code == 200
    assert empty.json() == []


def test_connect_rejects_unknown_provider_code(client):
    token = _register(client)
    response = client.post(
        "/api/v1/providers/connect",
        json={"provider_code": "NOT_A_REAL_PROVIDER", "external_account_ref": "acct-1"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 404


def test_connect_succeeds_for_a_catalog_provider(client):
    token = _register(client)
    response = client.post(
        "/api/v1/providers/connect",
        json={"provider_code": "AIRTEL", "external_account_ref": uuid.uuid4().hex},
        headers=_auth_headers(token),
    )
    assert response.status_code == 201, response.text
    assert response.json()["provider_code"] == "AIRTEL"
