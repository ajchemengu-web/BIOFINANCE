"""
Phase 6 — End-to-End Demonstration (docs/roadmap.md, PRD §47 success
criteria): walks the full path — customer creates a BioID, connects a
provider, sets routing policy; a merchant identifies the customer by
their BioFinance ID (BioFinance ID push pairing) and opens a payment
request; BioRouter routes it; the transaction completes; both sides see
the result.

What this does and doesn't prove:
- Every step below hits a real endpoint against a real PostgreSQL database
  (auth, BioID, providers, routing, merchant auth, merchant devices,
  BioRouter, the transaction state machine, transaction history) — none of
  it is mocked at the HTTP-request level the way test_push_service.py or
  test_daraja_provider.py are.
- MPESA routes to the in-memory mock provider, not real Daraja — no
  Safaricom sandbox credentials have been available in any session this
  project has been worked in (see docs/roadmap.md Phase 4). This
  demonstrates the whole BioFinance-side path is wired correctly; it does
  NOT verify the real Daraja integration, which is a separate, still-open
  item.
- This is the backend only. Nothing here drives the actual Flutter apps
  (mobile/, biopos/) — "the customer authenticates via device biometrics"
  below is representative of what the Flutter client does before calling
  these same endpoints, not something this script itself performs.

Run against a live backend (`uvicorn app.main:app --reload` from backend/,
per README):

    python -m scripts.demo_end_to_end

Or import run_demo(client) directly — tests/test_end_to_end_demo.py does
this against the TestClient fixture, so this exact flow is covered by the
regular test suite, not just an unverified standalone script.
"""

from __future__ import annotations

import sys
import uuid
from decimal import Decimal


def _step(verbose: bool, message: str) -> None:
    if verbose:
        print(f"  {message}")


def run_demo(client, *, verbose: bool = True) -> dict:
    """
    Runs the full Phase 6 story against `client` (an httpx.Client or
    Starlette TestClient — both expose the same .post/.get signature).
    Returns a dict of key artifacts (ids, the BioFinance ID code, the
    final transaction) for a caller that wants to inspect more than the
    printed narrative. Raises AssertionError at the first step that
    doesn't behave as the PRD §47 success criteria requires.
    """
    unique = uuid.uuid4().hex[:8]

    # 1. Customer creates a BioID.
    _step(verbose, "1. Customer registers — BioFinance issues a BioID automatically.")
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"demo-customer-{unique}@biofinance.dev",
            "password": "password123",
            "full_name": "Demo Customer",
        },
    )
    assert register_response.status_code == 201, register_response.text
    customer_token = register_response.json()["access_token"]
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    # "Authenticates via device biometrics" happens client-side in the
    # Flutter app before it ever calls the backend (docs/security-model.md
    # — raw biometric data never leaves the device); the access token
    # above is what that authentication produces. GET /bioid stands in
    # for the customer's app confirming its own identity.
    bioid_response = client.get("/api/v1/bioid", headers=customer_headers)
    assert bioid_response.status_code == 200, bioid_response.text
    bio_id_code = bioid_response.json()["code"]
    _step(verbose, f"   BioFinance ID issued: {bio_id_code}")

    # 2. Customer connects a provider and sees a balance.
    _step(verbose, "2. Customer connects M-PESA and sees a connected balance.")
    connect_response = client.post(
        "/api/v1/providers/connect",
        json={"provider_code": "MPESA", "external_account_ref": f"MPESA-{unique}"},
        headers=customer_headers,
    )
    assert connect_response.status_code == 201, connect_response.text
    mpesa_connection_id = connect_response.json()["id"]

    balances_response = client.get("/api/v1/balances", headers=customer_headers)
    assert balances_response.status_code == 200, balances_response.text
    assert any(b["provider_code"] == "MPESA" for b in balances_response.json()["by_provider"])
    _step(verbose, f"   BioWallet shows: {balances_response.json()}")

    # 3. Customer sets M-PESA as their preferred (primary) provider.
    _step(verbose, "3. Customer sets M-PESA as their preferred routing provider.")
    routing_response = client.put(
        "/api/v1/routing-policy",
        json={"mode": "PRIMARY", "primary_provider_id": mpesa_connection_id},
        headers=customer_headers,
    )
    assert routing_response.status_code == 200, routing_response.text

    # 4. A merchant registers, authenticates, and registers its terminal.
    _step(verbose, "4. Merchant registers and registers its terminal device.")
    merchant_register_response = client.post(
        "/api/v1/merchants/register",
        json={
            "business_name": "Demo Java House",
            "email": f"demo-merchant-{unique}@biofinance.dev",
            "password": "password123",
        },
    )
    assert merchant_register_response.status_code == 201, merchant_register_response.text
    merchant_token = merchant_register_response.json()["access_token"]
    merchant_headers = {"Authorization": f"Bearer {merchant_token}"}

    device_identifier = f"pos-terminal-{unique}"
    device_response = client.post(
        "/api/v1/merchant-devices/register",
        json={"device_identifier": device_identifier},
        headers=merchant_headers,
    )
    assert device_response.status_code == 200, device_response.text

    # 5. Merchant identifies the customer by their BioFinance ID and opens
    #    a payment request — this is the "BioFinance identifies the user"
    #    step from PRD §47, via BioFinance ID push pairing
    #    (docs/architecture.md) rather than a blind/open request.
    _step(verbose, f"5. Merchant creates a payment request targeted at BioFinance ID {bio_id_code}.")
    request_response = client.post(
        "/api/v1/payments/request",
        json={"amount": "450.00", "currency": "KES", "bio_id_code": bio_id_code},
        headers={
            **merchant_headers,
            "Idempotency-Key": f"TX-DEMO-{unique}",
            "Device-Identifier": device_identifier,
        },
    )
    assert request_response.status_code == 201, request_response.text
    transaction_id = request_response.json()["id"]
    assert request_response.json()["status"] == "AUTHENTICATION_PENDING"
    _step(verbose, f"   Request {transaction_id} opened, awaiting the customer's confirmation.")

    # 6. Customer claims the request — this is the moment BioRouter picks
    #    a provider and routes the payment (PRD §47: "BioRouter selects
    #    M-PESA → the Daraja adapter initiates the transaction" — the mock
    #    provider stands in for Daraja here, see the module docstring).
    _step(verbose, "6. Customer confirms (claim) — BioRouter selects M-PESA and routes the payment.")
    claim_response = client.post(f"/api/v1/payments/{transaction_id}/claim", headers=customer_headers)
    assert claim_response.status_code == 200, claim_response.text
    claimed = claim_response.json()
    assert claimed["status"] == "COMPLETED", f"expected COMPLETED, got {claimed['status']}"
    assert claimed["selected_provider"] == "MPESA"
    _step(verbose, f"   Transaction {transaction_id} reached COMPLETED via {claimed['selected_provider']}.")

    # 7. Merchant polls and sees the successful outcome.
    _step(verbose, "7. Merchant polls the request and sees PAYMENT SUCCESSFUL.")
    poll_response = client.get(f"/api/v1/payments/{transaction_id}")
    assert poll_response.status_code == 200, poll_response.text
    assert poll_response.json()["status"] == "COMPLETED"
    _step(verbose, "   Merchant terminal: PAYMENT SUCCESSFUL.")

    # 8. Customer sees it in their transaction history.
    _step(verbose, "8. Customer sees the payment in their transaction history.")
    history_response = client.get("/api/v1/transactions", headers=customer_headers)
    assert history_response.status_code == 200, history_response.text
    history_ids = {t["id"] for t in history_response.json()}
    assert transaction_id in history_ids
    _step(verbose, f"   Transaction {transaction_id} present in customer history ({len(history_ids)} total).")

    if verbose:
        print("\n  All PRD §47 success-criteria steps passed (mock MPESA standing in for Daraja).")

    return {
        "customer_token": customer_token,
        "merchant_token": merchant_token,
        "bio_id_code": bio_id_code,
        "transaction_id": transaction_id,
        "transaction": claimed,
        "amount": Decimal("450.00"),
    }


def main() -> None:
    import httpx

    base_url = "http://localhost:8000"
    print(f"Phase 6 end-to-end demonstration — against {base_url}\n")
    try:
        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            run_demo(client)
    except httpx.ConnectError:
        print(
            f"\nCouldn't reach {base_url} — start the backend first: "
            "`cd backend && uvicorn app.main:app --reload` (see README)."
        )
        sys.exit(1)
    except AssertionError as exc:
        print(f"\nDemo failed at an assertion: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
