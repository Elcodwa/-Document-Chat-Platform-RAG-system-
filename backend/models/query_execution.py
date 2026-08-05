import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class QueryExecution(Base):
    """
    A full record of one Text-to-SQL execution attempt - generated SQL,
    normalized/validated SQL, whether it passed validation, what tables it
    touched, and how execution went. This is what makes every database
    answer traceable back to a concrete, auditable query (see acceptance
    criterion "Traceability").
    """

    __tablename__ = "query_executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL")
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"))
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("database_connections.id", ondelete="CASCADE"), nullable=False
    )

    generated_sql: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_sql: Mapped[str | None] = mapped_column(Text)
    validation_status: Mapped[str] = mapped_column(String(30), nullable=False)  # "passed" | "blocked"
    validation_errors: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    applied_row_filters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    referenced_tables: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    execution_status: Mapped[str | None] = mapped_column(String(30))  # "success" | "error" | "not_executed"
    execution_time_ms: Mapped[int | None] = mapped_column(Integer)
    returned_row_count: Mapped[int | None] = mapped_column(Integer)
    result_preview: Mapped[dict | None] = mapped_column(JSONB)
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
