from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from schemas.common import ORMBase


class CreateKnowledgeBaseRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class KnowledgeBaseResponse(ORMBase):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    file_count: int = 0


class FileResponse(ORMBase):
    id: UUID
    knowledge_base_id: UUID | None
    original_name: str
    extension: str | None
    file_size_bytes: int | None
    processing_status: str
    processing_error: str | None
    page_count: int | None
    created_at: datetime
