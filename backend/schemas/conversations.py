from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from schemas.common import ORMBase


class CreateConversationRequest(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    active_connection_ids: list[UUID] = Field(default_factory=list)
    active_knowledge_base_ids: list[UUID] = Field(default_factory=list)


class UpdateConversationSourcesRequest(BaseModel):
    active_connection_ids: list[UUID] = Field(default_factory=list)
    active_knowledge_base_ids: list[UUID] = Field(default_factory=list)


class ConversationResponse(ORMBase):
    id: UUID
    title: str | None
    status: str
    active_connection_ids: list
    active_knowledge_base_ids: list
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class CitationResponse(ORMBase):
    id: UUID
    citation_type: str
    file_id: UUID | None
    title: str | None
    source_reference: str | None
    page_number: int | None
    relevance_score: float | None


class MessageResponse(ORMBase):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    detected_intent: str | None
    status: str
    error_message: str | None
    created_at: datetime
    citations: list[CitationResponse] = []


class QueryExecutionResponse(ORMBase):
    id: UUID
    connection_id: UUID
    generated_sql: str
    normalized_sql: str | None
    validation_status: str
    validation_errors: list
    referenced_tables: list
    execution_status: str | None
    execution_time_ms: int | None
    returned_row_count: int | None
    result_preview: dict | None
    error_message: str | None
