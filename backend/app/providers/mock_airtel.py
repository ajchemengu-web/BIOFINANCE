"""In-memory fake Airtel Money provider used until a real Airtel integration exists."""

import uuid
from decimal import Decimal

from app.providers.base import BalanceResult, PaymentProvider, PaymentRequest, PaymentResult


class MockAirtelProvider(PaymentProvider):
    code = "AIRTEL"

    def __init__(self) -> None:
        self._balances: dict[str, Decimal] = {}
        self._payments: dict[str, PaymentResult] = {}

    async def get_balance(self, account_id: str) -> BalanceResult:
        amount = self._balances.setdefault(account_id, Decimal("2150.00"))
        return BalanceResult(account_id=account_id, amount=amount)

    async def initiate_payment(self, request: PaymentRequest) -> PaymentResult:
        balance = self._balances.setdefault(request.account_id, Decimal("2150.00"))
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
