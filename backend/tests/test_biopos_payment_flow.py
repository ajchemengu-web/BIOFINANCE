"""
End-to-end test of the merchant-initiated payment flow BioPOS needs
(docs/roadmap.md Phase 5): a merchant, authenticated with its own
credentials, creates a payment request with no customer identified yet, a
customer claims it in their own session, and it routes through BioRouter
exactly like a customer-initiated payment. Same real-PostgreSQL
requirement as test_payment_flow.py.
"""

import json
import uuid

import respx
from httpx import Response

from app.core.config import Settings
from tests.conftest import fake_fcm_service_account_json


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


_DEFAULT_DEVICE = "device-1"


def _create_merchant(client) -> tuple[str, str]:
    """Returns (merchant_id, merchant_access_token). Also registers a
    default terminal (_DEFAULT_DEVICE) so _create_request/_create_request_response
    work out of the box — merchant_devices enforcement (docs/roadmap.md
    Phase 5, "Merchant-side integrity") requires one registered device
    before POST /payments/request will accept anything from this merchant."""
    email = f"merchant-{uuid.uuid4().hex[:8]}@biofinance.dev"
    response = client.post(
        "/api/v1/merchants/register",
        json={"business_name": "Naivas", "email": email, "password": "password123"},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]

    device_response = client.post(
        "/api/v1/merchant-devices/register",
        json={"device_identifier": _DEFAULT_DEVICE},
        headers=_auth_headers(token),
    )
    assert device_response.status_code == 200, device_response.text

    profile = client.get("/api/v1/merchants/me", headers=_auth_headers(token))
    assert profile.status_code == 200, profile.text
    return profile.json()["id"], token


def _create_request_response(
    client,
    merchant_token: str,
    amount: str = "2000.00",
    bio_id_code: str | None = None,
    device_identifier: str = _DEFAULT_DEVICE,
):
    payload = {"amount": amount, "currency": "KES"}
    if bio_id_code is not None:
        payload["bio_id_code"] = bio_id_code
    return client.post(
        "/api/v1/payments/request",
        json=payload,
        headers={
            **_auth_headers(merchant_token),
            "Idempotency-Key": f"TX-{uuid.uuid4().hex}",
            "Device-Identifier": device_identifier,
        },
    )


def _create_request(client, merchant_token: str, amount: str = "2000.00", bio_id_code: str | None = None) -> dict:
    response = _create_request_response(client, merchant_token, amount, bio_id_code)
    assert response.status_code == 201, response.text
    return response.json()


def _bio_id_code(client, token: str) -> str:
    response = client.get("/api/v1/bioid", headers=_auth_headers(token))
    assert response.status_code == 200, response.text
    return response.json()["code"]


def test_request_starts_awaiting_customer(client):
    merchant_id, merchant_token = _create_merchant(client)
    body = _create_request(client, merchant_token)

    assert body["status"] == "AUTHENTICATION_PENDING"
    assert body["selected_provider"] is None
    assert body["merchant_id"] == merchant_id


def test_request_requires_merchant_authentication(client):
    response = client.post(
        "/api/v1/payments/request",
        json={"amount": "500.00", "currency": "KES"},
        headers={"Idempotency-Key": f"TX-{uuid.uuid4().hex}", "Device-Identifier": _DEFAULT_DEVICE},
    )
    assert response.status_code in (401, 403)


def test_request_requires_a_device_identifier_header(client):
    _, merchant_token = _create_merchant(client)

    response = client.post(
        "/api/v1/payments/request",
        json={"amount": "500.00", "currency": "KES"},
        headers={**_auth_headers(merchant_token), "Idempotency-Key": f"TX-{uuid.uuid4().hex}"},
    )
    assert response.status_code == 422


def test_request_rejects_an_unregistered_device(client):
    _, merchant_token = _create_merchant(client)

    response = _create_request_response(client, merchant_token, device_identifier="a-device-never-registered")
    assert response.status_code == 403


def test_request_rejects_a_device_registered_to_a_different_merchant(client):
    """A device_identifier registered to merchant A must not authorize
    requests for merchant B, even with merchant B's own valid token — the
    check is scoped to the (merchant_id, device_identifier) pair, not the
    device identifier string alone."""
    _, token_a = _create_merchant(client)
    _, token_b = _create_merchant(client)

    register_response = client.post(
        "/api/v1/merchant-devices/register",
        json={"device_identifier": "shared-device-id"},
        headers=_auth_headers(token_a),
    )
    assert register_response.status_code == 200, register_response.text

    response = _create_request_response(client, token_b, device_identifier="shared-device-id")
    assert response.status_code == 403


def test_customer_claims_request_and_it_routes(client):
    token = _register(client)
    mpesa_id = _connect(client, token, "MPESA", uuid.uuid4().hex)
    client.put(
        "/api/v1/routing-policy",
        json={"mode": "PRIMARY", "primary_provider_id": mpesa_id},
        headers=_auth_headers(token),
    )
    _, merchant_token = _create_merchant(client)
    request_body = _create_request(client, merchant_token)

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
    _, merchant_token = _create_merchant(client)
    request_body = _create_request(client, merchant_token)

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
    _, merchant_token = _create_merchant(client)
    request_body = _create_request(client, merchant_token)

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
    _, merchant_token = _create_merchant(client)
    request_body = _create_request(client, merchant_token)

    poll_response = client.get(f"/api/v1/payments/{request_body['id']}")
    assert poll_response.status_code == 200
    assert poll_response.json()["status"] == "AUTHENTICATION_PENDING"


def test_merchant_cancels_its_own_request(client):
    _, merchant_token = _create_merchant(client)
    request_body = _create_request(client, merchant_token)

    response = client.post(
        f"/api/v1/payments/{request_body['id']}/cancel", headers=_auth_headers(merchant_token)
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "CANCELLED"


def test_merchant_cannot_cancel_another_merchants_request(client):
    _, owner_token = _create_merchant(client)
    _, other_token = _create_merchant(client)
    request_body = _create_request(client, owner_token)

    response = client.post(
        f"/api/v1/payments/{request_body['id']}/cancel", headers=_auth_headers(other_token)
    )
    assert response.status_code == 403


def test_cancel_requires_merchant_authentication(client):
    _, merchant_token = _create_merchant(client)
    request_body = _create_request(client, merchant_token)

    response = client.post(f"/api/v1/payments/{request_body['id']}/cancel")
    assert response.status_code in (401, 403)


def test_request_with_unknown_bio_id_code_returns_404(client):
    _, merchant_token = _create_merchant(client)

    response = _create_request_response(client, merchant_token, bio_id_code="BF-NOTREAL")
    assert response.status_code == 404


def test_targeted_request_is_claimed_by_the_matching_customer(client):
    """BioFinance ID push pairing: merchant enters the customer's BioFinance
    ID at creation, and that exact customer's session can still claim and
    route it — same as the open-claim path once they're identified."""
    token = _register(client)
    mpesa_id = _connect(client, token, "MPESA", uuid.uuid4().hex)
    client.put(
        "/api/v1/routing-policy",
        json={"mode": "PRIMARY", "primary_provider_id": mpesa_id},
        headers=_auth_headers(token),
    )
    _, merchant_token = _create_merchant(client)
    code = _bio_id_code(client, token)
    request_body = _create_request(client, merchant_token, bio_id_code=code)
    assert request_body["status"] == "AUTHENTICATION_PENDING"

    claim_response = client.post(
        f"/api/v1/payments/{request_body['id']}/claim",
        headers=_auth_headers(token),
    )
    assert claim_response.status_code == 200, claim_response.text
    assert claim_response.json()["status"] == "COMPLETED"


def test_targeted_request_rejects_a_different_customer(client):
    """The whole point of push pairing: a stranger with a valid session
    can't claim a request that was opened for someone else's BioFinance ID."""
    target_token = _register(client)
    stranger_token = _register(client)
    _, merchant_token = _create_merchant(client)
    code = _bio_id_code(client, target_token)
    request_body = _create_request(client, merchant_token, bio_id_code=code)

    response = client.post(
        f"/api/v1/payments/{request_body['id']}/claim",
        headers=_auth_headers(stranger_token),
    )
    assert response.status_code == 403


def test_pending_list_includes_a_targeted_request_awaiting_this_customer(client):
    token = _register(client)
    _, merchant_token = _create_merchant(client)
    code = _bio_id_code(client, token)
    request_body = _create_request(client, merchant_token, bio_id_code=code)

    response = client.get("/api/v1/payments/pending", headers=_auth_headers(token))
    assert response.status_code == 200, response.text
    ids = {t["id"] for t in response.json()}
    assert request_body["id"] in ids


def test_pending_list_excludes_another_customers_targeted_request(client):
    target_token = _register(client)
    stranger_token = _register(client)
    _, merchant_token = _create_merchant(client)
    code = _bio_id_code(client, target_token)
    request_body = _create_request(client, merchant_token, bio_id_code=code)

    response = client.get("/api/v1/payments/pending", headers=_auth_headers(stranger_token))
    assert response.status_code == 200, response.text
    assert request_body["id"] not in {t["id"] for t in response.json()}


def test_pending_list_excludes_open_untargeted_requests(client):
    """An open request (no bio_id_code) has no owner until someone claims
    it — it shouldn't show up as "pending for me" just because I'm logged
    in; that would let any authenticated user discover every open request."""
    token = _register(client)
    _, merchant_token = _create_merchant(client)
    request_body = _create_request(client, merchant_token)  # no bio_id_code

    response = client.get("/api/v1/payments/pending", headers=_auth_headers(token))
    assert response.status_code == 200, response.text
    assert request_body["id"] not in {t["id"] for t in response.json()}


def test_pending_list_drops_a_request_once_claimed(client):
    token = _register(client)
    _, merchant_token = _create_merchant(client)
    code = _bio_id_code(client, token)
    request_body = _create_request(client, merchant_token, bio_id_code=code)

    client.post(f"/api/v1/payments/{request_body['id']}/claim", headers=_auth_headers(token))

    response = client.get("/api/v1/payments/pending", headers=_auth_headers(token))
    assert response.status_code == 200, response.text
    assert request_body["id"] not in {t["id"] for t in response.json()}


@respx.mock
def test_targeted_request_sends_a_push_to_the_customers_registered_device(client, monkeypatch):
    """Wiring test: create_payment_request actually calls PushService when
    FCM is configured and the target customer has a registered device —
    not just that PushService itself works in isolation
    (test_push_service.py already covers that)."""
    fcm_settings = Settings(
        fcm_project_id="test-project", fcm_service_account_json=fake_fcm_service_account_json()
    )
    monkeypatch.setattr("app.services.payment_service.get_settings", lambda: fcm_settings)
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=Response(200, json={"access_token": "fake-token", "expires_in": 3599})
    )
    send_route = respx.post("https://fcm.googleapis.com/v1/projects/test-project/messages:send").mock(
        return_value=Response(200, json={"name": "projects/test-project/messages/1"})
    )

    token = _register(client)
    device_response = client.post(
        "/api/v1/devices/register",
        json={"device_identifier": "device-1", "push_token": "customer-push-token", "platform": "ANDROID"},
        headers=_auth_headers(token),
    )
    assert device_response.status_code == 200, device_response.text

    _, merchant_token = _create_merchant(client)
    code = _bio_id_code(client, token)
    request_body = _create_request(client, merchant_token, bio_id_code=code)

    assert send_route.called
    sent_body = json.loads(send_route.calls.last.request.content)
    assert sent_body["message"]["token"] == "customer-push-token"
    assert sent_body["message"]["data"]["transaction_id"] == request_body["id"]


def test_targeted_request_without_a_registered_device_still_succeeds(client):
    """No push_token registered — create_payment_request must not fail or
    even try to send; FCM isn't configured in the default test settings
    either, so this also covers that no-op path."""
    token = _register(client)
    _, merchant_token = _create_merchant(client)
    code = _bio_id_code(client, token)

    request_body = _create_request(client, merchant_token, bio_id_code=code)
    assert request_body["status"] == "AUTHENTICATION_PENDING"


def test_repeated_requests_against_the_same_bio_id_code_are_rate_limited(client):
    """Abuse surface documented in docs/security-model.md: a merchant (or
    anyone who's guessed a valid BioFinance ID) spamming push-pairing
    requests against one person. 5 per 60s per bio_id_code
    (app/services/payment_service.py) — each call here uses its own
    idempotency key so the limiter, not the idempotency short-circuit, is
    what's under test."""
    token = _register(client)
    _, merchant_token = _create_merchant(client)
    code = _bio_id_code(client, token)

    responses = [_create_request_response(client, merchant_token, bio_id_code=code) for _ in range(6)]

    assert [r.status_code for r in responses[:5]] == [201] * 5
    assert responses[5].status_code == 429


def test_request_creation_is_idempotent(client):
    _, merchant_token = _create_merchant(client)
    idempotency_key = f"TX-{uuid.uuid4().hex}"

    first = client.post(
        "/api/v1/payments/request",
        json={"amount": "500.00", "currency": "KES"},
        headers={
            **_auth_headers(merchant_token),
            "Idempotency-Key": idempotency_key,
            "Device-Identifier": _DEFAULT_DEVICE,
        },
    )
    second = client.post(
        "/api/v1/payments/request",
        json={"amount": "500.00", "currency": "KES"},
        headers={
            **_auth_headers(merchant_token),
            "Idempotency-Key": idempotency_key,
            "Device-Identifier": _DEFAULT_DEVICE,
        },
    )
    assert first.status_code == 201, first.text
    assert first.json()["id"] == second.json()["id"]
