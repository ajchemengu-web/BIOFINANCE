import pytest
from fastapi.testclient import TestClient

from app.main import app


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
