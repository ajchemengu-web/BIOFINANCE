import uuid

from pydantic import BaseModel


class MerchantDeviceRegisterRequest(BaseModel):
    device_identifier: str


class MerchantDeviceResponse(BaseModel):
    id: uuid.UUID
    device_identifier: str
    status: str

    model_config = {"from_attributes": True}
