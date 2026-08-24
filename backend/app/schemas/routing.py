import uuid

from pydantic import BaseModel


class RoutingPolicyUpdate(BaseModel):
    mode: str  # PRIMARY, PRIORITY, AUTOMATIC, MANUAL
    primary_provider_id: uuid.UUID | None = None
    fallback_provider_id: uuid.UUID | None = None


class RoutingPolicyResponse(BaseModel):
    mode: str
    primary_provider_id: uuid.UUID | None
    fallback_provider_id: uuid.UUID | None

    model_config = {"from_attributes": True}
