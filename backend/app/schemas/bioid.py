import uuid

from pydantic import BaseModel


class BioIDResponse(BaseModel):
    id: uuid.UUID
    code: str
    status: str

    model_config = {"from_attributes": True}
