"""
Real merchant authentication (docs/roadmap.md Phase 5, docs/security-model.md
"Merchant-side integrity") — register/login issuing a merchant-scoped JWT
distinct from the customer users token, per app/core/deps.py get_current_merchant.
"""

import uuid


def _register_payload() -> dict:
    return {
        "business_name": "Java House",
        "email": f"merchant-{uuid.uuid4().hex[:8]}@biofinance.dev",
        "password": "password123",
    }


def test_register_returns_tokens(client):
    response = client.post("/api/v1/merchants/register", json=_register_payload())
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]


def test_register_rejects_duplicate_email(client):
    payload = _register_payload()
    first = client.post("/api/v1/merchants/register", json=payload)
    assert first.status_code == 201, first.text

    second = client.post("/api/v1/merchants/register", json=payload)
    assert second.status_code == 409


def test_login_with_correct_credentials(client):
    payload = _register_payload()
    client.post("/api/v1/merchants/register", json=payload)

    response = client.post(
        "/api/v1/merchants/login", json={"email": payload["email"], "password": payload["password"]}
    )
    assert response.status_code == 200, response.text
    assert response.json()["access_token"]


def test_login_with_wrong_password_is_rejected(client):
    payload = _register_payload()
    client.post("/api/v1/merchants/register", json=payload)

    response = client.post(
        "/api/v1/merchants/login", json={"email": payload["email"], "password": "not-the-password"}
    )
    assert response.status_code == 401


def test_login_with_unknown_email_is_rejected(client):
    response = client.post(
        "/api/v1/merchants/login", json={"email": "nobody@biofinance.dev", "password": "password123"}
    )
    assert response.status_code == 401


def test_me_returns_the_authenticated_merchants_profile(client):
    payload = _register_payload()
    register_response = client.post("/api/v1/merchants/register", json=payload)
    token = register_response.json()["access_token"]

    response = client.get("/api/v1/merchants/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    assert response.json()["business_name"] == "Java House"


def test_me_requires_a_merchant_token_not_a_customer_token(client):
    """A customer's own access token must be structurally rejected here —
    not just "wrong merchant", a completely different token type
    (docs/security-model.md)."""
    email = f"user-{uuid.uuid4().hex[:8]}@biofinance.dev"
    customer_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": "Test User"},
    )
    customer_token = customer_response.json()["access_token"]

    response = client.get("/api/v1/merchants/me", headers={"Authorization": f"Bearer {customer_token}"})
    assert response.status_code == 401


def test_merchant_token_cannot_be_used_on_customer_endpoints(client):
    """The reverse of the above — a merchant's token must be rejected by
    customer-scoped endpoints like GET /bioid."""
    register_response = client.post("/api/v1/merchants/register", json=_register_payload())
    merchant_token = register_response.json()["access_token"]

    response = client.get("/api/v1/bioid", headers={"Authorization": f"Bearer {merchant_token}"})
    assert response.status_code == 401
