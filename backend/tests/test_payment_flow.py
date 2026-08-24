"""
End-to-end test of the Phase 2/3 path: register -> connect providers -> set
routing policy -> pay -> fallback on decline -> idempotency -> history.
Requires a real DATABASE_URL with migrations applied (see README) — this
exercises actual PostgreSQL, not a mock.
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


def _connect(client, token: str, provider_code: str, account_ref: str) -> str:
    response = client.post(
        "/api/v1/providers/connect",
        json={"provider_code": provider_code, "external_account_ref": account_ref},
        headers=_auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_merchant(client) -> str:
    response = client.post("/api/v1/merchants", json={"business_name": "Java House"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_payment_succeeds_via_primary_provider(client):
    token = _register(client)
    account_ref = uuid.uuid4().hex
    mpesa_connection_id = _connect(client, token, "MPESA", account_ref)
    merchant_id = _create_merchant(client)

    routing_response = client.put(
        "/api/v1/routing-policy",
        json={"mode": "PRIMARY", "primary_provider_id": mpesa_connection_id},
        headers=_auth_headers(token),
    )
    assert routing_response.status_code == 200, routing_response.text

    payment_response = client.post(
        "/api/v1/payments",
        json={"merchant_id": merchant_id, "amount": "450.00", "currency": "KES"},
        headers={**_auth_headers(token), "Idempotency-Key": f"TX-{uuid.uuid4().hex}"},
    )
    assert payment_response.status_code == 201, payment_response.text
    body = payment_response.json()
    assert body["status"] == "COMPLETED"
    assert body["selected_provider"] == "MPESA"


def test_idempotency_key_returns_existing_transaction(client):
    token = _register(client)
    account_ref = uuid.uuid4().hex
    mpesa_connection_id = _connect(client, token, "MPESA", account_ref)
    merchant_id = _create_merchant(client)
    client.put(
        "/api/v1/routing-policy",
        json={"mode": "PRIMARY", "primary_provider_id": mpesa_connection_id},
        headers=_auth_headers(token),
    )

    idempotency_key = f"TX-{uuid.uuid4().hex}"
    first = client.post(
        "/api/v1/payments",
        json={"merchant_id": merchant_id, "amount": "100.00", "currency": "KES"},
        headers={**_auth_headers(token), "Idempotency-Key": idempotency_key},
    )
    second = client.post(
        "/api/v1/payments",
        json={"merchant_id": merchant_id, "amount": "100.00", "currency": "KES"},
        headers={**_auth_headers(token), "Idempotency-Key": idempotency_key},
    )
    assert first.json()["id"] == second.json()["id"]


def test_falls_back_when_primary_provider_declines(client):
    token = _register(client)
    mpesa_id = _connect(client, token, "MPESA", uuid.uuid4().hex)
    equity_id = _connect(client, token, "EQUITY", uuid.uuid4().hex)
    merchant_id = _create_merchant(client)

    client.put(
        "/api/v1/routing-policy",
        json={"mode": "PRIMARY", "primary_provider_id": mpesa_id, "fallback_provider_id": equity_id},
        headers=_auth_headers(token),
    )

    # MockMpesaProvider seeds each account at KSh 8500 — exceed it to force a decline.
    payment_response = client.post(
        "/api/v1/payments",
        json={"merchant_id": merchant_id, "amount": "9000.00", "currency": "KES"},
        headers={**_auth_headers(token), "Idempotency-Key": f"TX-{uuid.uuid4().hex}"},
    )
    assert payment_response.status_code == 201, payment_response.text
    body = payment_response.json()
    assert body["status"] == "COMPLETED"
    assert body["selected_provider"] == "EQUITY"


def test_transaction_appears_in_history(client):
    token = _register(client)
    mpesa_id = _connect(client, token, "MPESA", uuid.uuid4().hex)
    merchant_id = _create_merchant(client)
    client.put(
        "/api/v1/routing-policy",
        json={"mode": "PRIMARY", "primary_provider_id": mpesa_id},
        headers=_auth_headers(token),
    )
    client.post(
        "/api/v1/payments",
        json={"merchant_id": merchant_id, "amount": "50.00", "currency": "KES"},
        headers={**_auth_headers(token), "Idempotency-Key": f"TX-{uuid.uuid4().hex}"},
    )

    history_response = client.get("/api/v1/transactions", headers=_auth_headers(token))
    assert history_response.status_code == 200
    transactions = history_response.json()
    assert len(transactions) == 1
    assert len(transactions[0]["attempts"]) == 1
