"""
BioRouter — attempts the primary provider from the user's routing policy,
falls back to the fallback provider on decline, and returns every attempt
made (for payment_attempts bookkeeping). See docs/architecture.md and PRD
§23. Takes prefetched connection/account data rather than querying the DB
itself, so the routing decision logic stays independently testable.
"""

from decimal import Decimal

from app.models.provider import ProviderConnection
from app.models.routing_policy import RoutingPolicy
from app.providers.base import PaymentRequest, PaymentResult
from app.providers.registry import get_provider


class RouterService:
    async def route_payment(
        self,
        policy: RoutingPolicy,
        connections_by_id: dict,
        account_ref_by_connection_id: dict,
        amount: Decimal,
        currency: str,
        reference: str,
    ) -> list[tuple[ProviderConnection, PaymentResult]]:
        attempts: list[tuple[ProviderConnection, PaymentResult]] = []

        candidate_ids = [
            provider_id
            for provider_id in (policy.primary_provider_id, policy.fallback_provider_id)
            if provider_id is not None
        ]

        for connection_id in candidate_ids:
            connection = connections_by_id.get(connection_id)
            if connection is None or connection.status != "CONNECTED":
                continue
            account_ref = account_ref_by_connection_id.get(connection_id)
            if account_ref is None:
                continue

            provider = get_provider(connection.provider_code)
            result = await provider.initiate_payment(
                PaymentRequest(
                    account_id=account_ref, amount=amount, currency=currency, reference=reference
                )
            )
            attempts.append((connection, result))
            if result.status == "SUCCESS":
                break

        return attempts
