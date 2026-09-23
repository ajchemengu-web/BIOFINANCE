import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    event_metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}
