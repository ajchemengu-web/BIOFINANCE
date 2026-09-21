import json

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.main import app


def fake_fcm_service_account_json() -> str:
    """A throwaway RSA keypair + service account shape for PushService
    tests — never a real Firebase credential. Shared so every test that
    needs a syntactically valid one doesn't generate its own keypair."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    return json.dumps({"client_email": "test@test-project.iam.gserviceaccount.com", "private_key": pem})


@pytest.fixture(scope="session")
def client():
    """
    Shared TestClient used as a context manager so all requests share one
    anyio portal/event loop for the test session. Without this, TestClient
    spins up a fresh event loop per call outside a `with` block, and the
    SQLAlchemy async engine's pooled asyncpg connection — created on the
    first loop — gets reused from a mismatched later loop, raising
    "cannot perform operation: another operation is in progress".
    """
    with TestClient(app) as test_client:
        yield test_client
