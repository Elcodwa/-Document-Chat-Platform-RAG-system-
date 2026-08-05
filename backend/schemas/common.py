from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(ORMBase):
    id: UUID
    created_at: datetime


class MessageResponse(BaseModel):
    message: str
