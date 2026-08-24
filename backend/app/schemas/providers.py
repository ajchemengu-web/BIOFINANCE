import uuid

from pydantic import BaseModel


class ProviderConnectRequest(BaseModel):
    provider_code: str
    external_account_ref: str


class ProviderConnectionResponse(BaseModel):
    id: uuid.UUID
    provider_code: str
    status: str

    model_config = {"from_attributes": True}
