"""
Generic in-memory mock, used for any provider_code in the catalog that
doesn't have a bespoke adapter (real or mock) registered in registry.py —
the whole point being that adding a provider to the catalog is enough to
demo-connect and route through it immediately, before a real integration
agreement exists. See docs/architecture.md "Provider catalog".
"""

import uuid
from decimal import Decimal

from app.providers.base import BalanceResult, PaymentProvider, PaymentRequest, PaymentResult

_DEFAULT_BALANCE = Decimal("5000.00")


class GenericMockProvider(PaymentProvider):
    def __init__(self, code: str) -> None:
        self.code = code
        self._balances: dict[str, Decimal] = {}
        self._payments: dict[str, PaymentResult] = {}

    async def get_balance(self, account_id: str) -> BalanceResult:
        amount = self._balances.setdefault(account_id, _DEFAULT_BALANCE)
        return BalanceResult(account_id=account_id, amount=amount)

    async def initiate_payment(self, request: PaymentRequest) -> PaymentResult:
        balance = self._balances.setdefault(request.account_id, _DEFAULT_BALANCE)
        provider_reference = str(uuid.uuid4())
        if balance >= request.amount:
            self._balances[request.account_id] = balance - request.amount
            result = PaymentResult(provider_reference=provider_reference, status="SUCCESS")
        else:
            result = PaymentResult(provider_reference=provider_reference, status="DECLINED")
        self._payments[provider_reference] = result
        return result

    async def get_payment_status(self, transaction_id: str) -> PaymentResult:
        return self._payments.get(
            transaction_id, PaymentResult(provider_reference=transaction_id, status="ERROR")
        )

    async def refund_payment(self, transaction_id: str) -> PaymentResult:
        return PaymentResult(provider_reference=transaction_id, status="SUCCESS")
