import uuid

from pydantic import BaseModel, EmailStr


class MerchantRegisterRequest(BaseModel):
    business_name: str
    email: EmailStr
    password: str


class MerchantLoginRequest(BaseModel):
    email: EmailStr
    password: str


class MerchantResponse(BaseModel):
    id: uuid.UUID
    business_name: str
    merchant_code: str
    status: str

    model_config = {"from_attributes": True}
