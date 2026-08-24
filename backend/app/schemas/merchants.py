import uuid

from pydantic import BaseModel


class MerchantCreateRequest(BaseModel):
    business_name: str


class MerchantResponse(BaseModel):
    id: uuid.UUID
    business_name: str
    merchant_code: str
    status: str

    model_config = {"from_attributes": True}
