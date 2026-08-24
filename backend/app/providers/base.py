"""
The provider abstraction. BioRouter and the payment/transaction services depend
only on this interface — never on a concrete provider SDK. Adding a new financial
provider means implementing this class, not touching BioRouter. See
docs/architecture.md "The non-negotiable rule".
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class BalanceResult:
    account_id: str
    amount: Decimal
    currency: str = "KES"


@dataclass
class PaymentRequest:
    account_id: str
    amount: Decimal
    currency: str
    reference: str  # BioFinance transaction id / idempotency key


@dataclass
class PaymentResult:
    provider_reference: str
    status: str  # SUCCESS, DECLINED, PENDING, TIMEOUT, ERROR
    raw: dict | None = None


class PaymentProvider(ABC):
    """Uniform interface every real or mock financial provider must implement."""

    code: str

    @abstractmethod
    async def get_balance(self, account_id: str) -> BalanceResult: ...

    @abstractmethod
    async def initiate_payment(self, request: PaymentRequest) -> PaymentResult: ...

    @abstractmethod
    async def get_payment_status(self, transaction_id: str) -> PaymentResult: ...

    @abstractmethod
    async def refund_payment(self, transaction_id: str) -> PaymentResult: ...
