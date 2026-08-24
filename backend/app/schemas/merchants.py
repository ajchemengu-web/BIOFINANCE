import uuid

from pydantic import BaseModel


class MerchantResponse(BaseModel):
    id: uuid.UUID
    business_name: str
    merchant_code: str
    status: str

    model_config = {"from_attributes": True}
