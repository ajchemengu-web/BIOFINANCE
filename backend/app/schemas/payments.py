import uuid
from decimal import Decimal

from pydantic import BaseModel


class PaymentCreateRequest(BaseModel):
    merchant_id: uuid.UUID
    amount: Decimal
    currency: str = "KES"


class PaymentResponse(BaseModel):
    id: uuid.UUID
    status: str
    amount: Decimal
    currency: str
    selected_provider: str | None

    model_config = {"from_attributes": True}
