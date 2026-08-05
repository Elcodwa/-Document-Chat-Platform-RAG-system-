"""
The shared state object threaded through every node in the graph. Each
node reads what it needs and returns a partial dict of updates - LangGraph
merges these into the running state between steps.
"""
import uuid
from typing import TypedDict


class DatabaseEvidence(TypedDict):
    connection_id: str
    connection_name: str
    generated_sql: str
    normalized_sql: str | None
    validation_status: str  # "passed" | "blocked"
    validation_errors: list[str]
    execution_status: str | None  # "success" | "error" | None
    columns: list[str]
    rows: list[dict]
    row_count: int
    referenced_tables: list[str]


class DocumentEvidence(TypedDict):
    file_id: str
    file_name: str
    chunk_id: str
    page_number: int | None
    content: str
    similarity: float


class AgentState(TypedDict, total=False):
    # --- inputs (set before the graph runs) ---
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    question: str
    conversation_history: list[dict]  # [{"role": "user"/"assistant", "content": "..."}]
    active_connection_ids: list[uuid.UUID]
    active_knowledge_base_ids: list[uuid.UUID]

    # --- populated during the run ---
    intent: str  # "database" | "document" | "hybrid" | "general"
    database_evidence: list[DatabaseEvidence]
    document_evidence: list[DocumentEvidence]
    final_answer: str
    model_name: str
