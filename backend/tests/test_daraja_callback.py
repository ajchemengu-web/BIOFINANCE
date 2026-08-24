"""
Tests PaymentService.handle_daraja_callback directly against the real
database. Building a Transaction that's actually AUTHORIZATION_PENDING via
the normal HTTP flow would require Daraja credentials wired through respx
end-to-end (create_payment -> router_service -> DarajaProvider.initiate_payment
via real HTTP endpoints) — this instead sets up that state directly, since
the callback handler itself is what's under test here, not the full STK
push round trip (already covered by test_daraja_provider.py).
"""

import uuid
from decimal import Decimal

import pytest

from app.db.database import async_session_factory
from app.models.bioid import BioID
from app.models.merchant import Merchant
from app.models.transaction import PaymentAttempt, Transaction
from app.models.user import User
from app.services.bioid_service import generate_bio_id_code
from app.services.payment_service import PaymentService


async def _create_pending_transaction(db, checkout_request_id: str) -> Transaction:
    user = User(
        email=f"daraja-test-{uuid.uuid4().hex[:8]}@biofinance.dev",
        password_hash="not-a-real-hash",
        full_name="Daraja Test User",
    )
    db.add(user)
    await db.flush()

    bio_id = BioID(user_id=user.id, code=generate_bio_id_code())
    db.add(bio_id)

    merchant = Merchant(business_name="Test Merchant", merchant_code=f"MC-{uuid.uuid4().hex[:6]}")
    db.add(merchant)
    await db.flush()

    transaction = Transaction(
        bio_id=bio_id.id,
        merchant_id=merchant.id,
        amount=Decimal("450.00"),
        currency="KES",
        status="AUTHORIZATION_PENDING",
        selected_provider="MPESA",
        idempotency_key=f"TX-{uuid.uuid4().hex}",
    )
    db.add(transaction)
    await db.flush()

    db.add(
        PaymentAttempt(
            transaction_id=transaction.id,
            provider_code="MPESA",
            result="PENDING",
            provider_reference=checkout_request_id,
        )
    )
    await db.commit()
    await db.refresh(transaction)
    return transaction


@pytest.mark.asyncio
async def test_callback_completes_transaction_on_success():
    checkout_request_id = f"checkout-{uuid.uuid4().hex}"
    async with async_session_factory() as db:
        transaction = await _create_pending_transaction(db, checkout_request_id)

        updated = await PaymentService(db).handle_daraja_callback(checkout_request_id, result_code=0)

        assert updated is not None
        assert updated.id == transaction.id
        assert updated.status == "COMPLETED"
        assert updated.completed_at is not None
        assert updated.selected_provider == "MPESA"


@pytest.mark.asyncio
async def test_callback_declines_transaction_on_nonzero_result_code():
    checkout_request_id = f"checkout-{uuid.uuid4().hex}"
    async with async_session_factory() as db:
        await _create_pending_transaction(db, checkout_request_id)

        updated = await PaymentService(db).handle_daraja_callback(checkout_request_id, result_code=1032)

        assert updated is not None
        assert updated.status == "DECLINED"
        assert updated.completed_at is None


@pytest.mark.asyncio
async def test_callback_for_unknown_checkout_id_is_a_no_op():
    async with async_session_factory() as db:
        result = await PaymentService(db).handle_daraja_callback("does-not-exist", result_code=0)
        assert result is None


@pytest.mark.asyncio
async def test_duplicate_callback_does_not_reopen_a_resolved_transaction():
    checkout_request_id = f"checkout-{uuid.uuid4().hex}"
    async with async_session_factory() as db:
        transaction = await _create_pending_transaction(db, checkout_request_id)
        await PaymentService(db).handle_daraja_callback(checkout_request_id, result_code=0)

        # Safaricom retries callbacks it thinks weren't delivered — a second
        # one for the same request must not flip an already-COMPLETED
        # transaction back to DECLINED.
        second = await PaymentService(db).handle_daraja_callback(checkout_request_id, result_code=1)

        await db.refresh(transaction)
        assert second is not None
        assert transaction.status == "COMPLETED"
