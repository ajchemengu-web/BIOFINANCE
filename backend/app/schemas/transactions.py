import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PaymentAttemptResponse(BaseModel):
    provider_code: str
    result: str
    provider_reference: str | None

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    id: uuid.UUID
    amount: Decimal
    currency: str
    status: str
    selected_provider: str | None
    created_at: datetime
    completed_at: datetime | None
    attempts: list[PaymentAttemptResponse] = []

    model_config = {"from_attributes": True}
