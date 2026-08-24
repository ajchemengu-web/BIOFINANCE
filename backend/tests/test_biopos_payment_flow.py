"""
End-to-end test of the merchant-initiated payment flow BioPOS needs
(docs/roadmap.md Phase 5): a merchant creates a payment request with no
customer identified yet, a customer claims it in their own session, and it
routes through BioRouter exactly like a customer-initiated payment. Same
real-PostgreSQL requirement as test_payment_flow.py.
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
    response = client.post("/api/v1/merchants", json={"business_name": "Naivas"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_request(client, merchant_id: str, amount: str = "2000.00") -> dict:
    response = client.post(
        "/api/v1/payments/request",
        json={"merchant_id": merchant_id, "amount": amount, "currency": "KES"},
        headers={"Idempotency-Key": f"TX-{uuid.uuid4().hex}"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_request_starts_awaiting_customer(client):
    merchant_id = _create_merchant(client)
    body = _create_request(client, merchant_id)

    assert body["status"] == "AUTHENTICATION_PENDING"
    assert body["selected_provider"] is None


def test_customer_claims_request_and_it_routes(client):
    token = _register(client)
    mpesa_id = _connect(client, token, "MPESA", uuid.uuid4().hex)
    client.put(
        "/api/v1/routing-policy",
        json={"mode": "PRIMARY", "primary_provider_id": mpesa_id},
        headers=_auth_headers(token),
    )
    merchant_id = _create_merchant(client)
    request_body = _create_request(client, merchant_id)

    claim_response = client.post(
        f"/api/v1/payments/{request_body['id']}/claim",
        headers=_auth_headers(token),
    )
    assert claim_response.status_code == 200, claim_response.text
    claimed = claim_response.json()
    assert claimed["id"] == request_body["id"]
    assert claimed["status"] == "COMPLETED"
    assert claimed["selected_provider"] == "MPESA"


def test_claimed_request_appears_in_the_claiming_customers_history(client):
    token = _register(client)
    mpesa_id = _connect(client, token, "MPESA", uuid.uuid4().hex)
    client.put(
        "/api/v1/routing-policy",
        json={"mode": "PRIMARY", "primary_provider_id": mpesa_id},
        headers=_auth_headers(token),
    )
    merchant_id = _create_merchant(client)
    request_body = _create_request(client, merchant_id)

    # Not the customer's yet — merchant just created it, nobody's claimed it.
    history_before = client.get("/api/v1/transactions", headers=_auth_headers(token))
    assert request_body["id"] not in {t["id"] for t in history_before.json()}

    client.post(f"/api/v1/payments/{request_body['id']}/claim", headers=_auth_headers(token))

    history_after = client.get("/api/v1/transactions", headers=_auth_headers(token))
    assert request_body["id"] in {t["id"] for t in history_after.json()}


def test_claiming_an_already_claimed_request_fails(client):
    token_a = _register(client)
    token_b = _register(client)
    mpesa_id = _connect(client, token_a, "MPESA", uuid.uuid4().hex)
    client.put(
        "/api/v1/routing-policy",
        json={"mode": "PRIMARY", "primary_provider_id": mpesa_id},
        headers=_auth_headers(token_a),
    )
    merchant_id = _create_merchant(client)
    request_body = _create_request(client, merchant_id)

    first_claim = client.post(
        f"/api/v1/payments/{request_body['id']}/claim", headers=_auth_headers(token_a)
    )
    assert first_claim.status_code == 200, first_claim.text

    second_claim = client.post(
        f"/api/v1/payments/{request_body['id']}/claim", headers=_auth_headers(token_b)
    )
    assert second_claim.status_code == 409


def test_claiming_a_nonexistent_request_returns_404(client):
    token = _register(client)
    response = client.post(
        f"/api/v1/payments/{uuid.uuid4()}/claim", headers=_auth_headers(token)
    )
    assert response.status_code == 404


def test_merchant_polls_status_via_get_without_customer_auth(client):
    """BioPOS has no customer session to attach — GET must stay open."""
    merchant_id = _create_merchant(client)
    request_body = _create_request(client, merchant_id)

    poll_response = client.get(f"/api/v1/payments/{request_body['id']}")
    assert poll_response.status_code == 200
    assert poll_response.json()["status"] == "AUTHENTICATION_PENDING"


def test_request_creation_is_idempotent(client):
    merchant_id = _create_merchant(client)
    idempotency_key = f"TX-{uuid.uuid4().hex}"

    first = client.post(
        "/api/v1/payments/request",
        json={"merchant_id": merchant_id, "amount": "500.00", "currency": "KES"},
        headers={"Idempotency-Key": idempotency_key},
    )
    second = client.post(
        "/api/v1/payments/request",
        json={"merchant_id": merchant_id, "amount": "500.00", "currency": "KES"},
        headers={"Idempotency-Key": idempotency_key},
    )
    assert first.json()["id"] == second.json()["id"]
