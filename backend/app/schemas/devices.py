import uuid
from typing import Literal

from pydantic import BaseModel


class DeviceRegisterRequest(BaseModel):
    device_identifier: str
    push_token: str | None = None
    platform: Literal["ANDROID", "IOS", "WEB"] | None = None


class DeviceResponse(BaseModel):
    id: uuid.UUID
    device_identifier: str
    platform: str | None
    status: str

    model_config = {"from_attributes": True}
