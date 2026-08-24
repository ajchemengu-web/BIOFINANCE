"""
Unit tests for the BioRouter fallback algorithm in isolation from the
database — RouterService.route_payment only needs prefetched dicts plus the
in-memory mock providers, both constructible without a session.
"""

import uuid
from decimal import Decimal

import pytest

from app.models.provider import ProviderConnection
from app.models.routing_policy import RoutingPolicy
from app.providers.registry import get_provider
from app.services.router_service import RouterService


def _connection(provider_code: str) -> ProviderConnection:
    connection = ProviderConnection(provider_code=provider_code, status="CONNECTED")
    connection.id = uuid.uuid4()
    return connection


@pytest.mark.asyncio
async def test_routes_to_primary_when_funds_sufficient():
    mpesa = _connection("MPESA")
    policy = RoutingPolicy(primary_provider_id=mpesa.id)
    account_ref = uuid.uuid4().hex

    attempts = await RouterService().route_payment(
        policy,
        {mpesa.id: mpesa},
        {mpesa.id: account_ref},
        Decimal("100.00"),
        "KES",
        "ref-1",
    )

    assert len(attempts) == 1
    connection, result = attempts[0]
    assert connection.provider_code == "MPESA"
    assert result.status == "SUCCESS"


@pytest.mark.asyncio
async def test_falls_back_when_primary_declines():
    mpesa = _connection("MPESA")
    equity = _connection("EQUITY")
    policy = RoutingPolicy(primary_provider_id=mpesa.id, fallback_provider_id=equity.id)
    mpesa_account = uuid.uuid4().hex
    equity_account = uuid.uuid4().hex

    # MockMpesaProvider seeds each account at KSh 8500 — exceed it to force a decline.
    attempts = await RouterService().route_payment(
        policy,
        {mpesa.id: mpesa, equity.id: equity},
        {mpesa.id: mpesa_account, equity.id: equity_account},
        Decimal("9000.00"),
        "KES",
        "ref-2",
    )

    assert [connection.provider_code for connection, _ in attempts] == ["MPESA", "EQUITY"]
    assert attempts[0][1].status == "DECLINED"
    assert attempts[1][1].status == "SUCCESS"

    # The decline shouldn't have touched Equity's balance.
    equity_balance = await get_provider("EQUITY").get_balance(equity_account)
    assert equity_balance.amount == Decimal("14200.00") - Decimal("9000.00")


@pytest.mark.asyncio
async def test_stops_after_first_success_without_trying_fallback():
    mpesa = _connection("MPESA")
    equity = _connection("EQUITY")
    policy = RoutingPolicy(primary_provider_id=mpesa.id, fallback_provider_id=equity.id)

    attempts = await RouterService().route_payment(
        policy,
        {mpesa.id: mpesa, equity.id: equity},
        {mpesa.id: uuid.uuid4().hex, equity.id: uuid.uuid4().hex},
        Decimal("50.00"),
        "KES",
        "ref-3",
    )

    assert len(attempts) == 1
    assert attempts[0][0].provider_code == "MPESA"


@pytest.mark.asyncio
async def test_no_attempts_when_policy_has_no_providers():
    policy = RoutingPolicy()

    attempts = await RouterService().route_payment(
        policy, {}, {}, Decimal("50.00"), "KES", "ref-4"
    )

    assert attempts == []
