import uuid
from decimal import Decimal

from pydantic import BaseModel


class PaymentCreateRequest(BaseModel):
    merchant_id: uuid.UUID
    amount: Decimal
    currency: str = "KES"


class PaymentRequestCreate(BaseModel):
    """Merchant-initiated (biopos/) — no customer session here, so identity
    comes either from the customer later (open claim, bio_id_code omitted)
    or from the merchant now (BioFinance ID push pairing, bio_id_code set —
    docs/roadmap.md Phase 5). Either way POST /payments/{id}/claim is what
    actually authenticates and routes it."""

    merchant_id: uuid.UUID
    amount: Decimal
    currency: str = "KES"
    bio_id_code: str | None = None


class PaymentResponse(BaseModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    status: str
    amount: Decimal
    currency: str
    selected_provider: str | None

    model_config = {"from_attributes": True}
