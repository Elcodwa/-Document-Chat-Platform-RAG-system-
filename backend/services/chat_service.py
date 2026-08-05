import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from agents.graph import build_graph
from agents.state import AgentState
from models.citation import MessageCitation
from models.conversation import Conversation
from models.message import Message
from models.query_execution import QueryExecution
from models.user import User
from repositories.message_repo import MessageRepository


def _initial_state(conversation: Conversation, user: User, question: str, history: list[dict]) -> AgentState:
    return {
        "tenant_id": conversation.tenant_id,
        "user_id": user.id,
        "question": question,
        "conversation_history": history,
        "active_connection_ids": [uuid.UUID(c) for c in conversation.active_connection_ids],
        "active_knowledge_base_ids": [uuid.UUID(k) for k in conversation.active_knowledge_base_ids],
        "database_evidence": [],
        "document_evidence": [],
    }


def _recent_history(db: Session, tenant_id: uuid.UUID, conversation_id: uuid.UUID, limit: int = 10) -> list[dict]:
    messages = MessageRepository(db).list_for_conversation(tenant_id, conversation_id)
    recent = messages[-limit:]
    return [{"role": m.role, "content": m.content} for m in recent]


def run_and_persist(db: Session, conversation: Conversation, user: User, question: str) -> Message:
    """Runs the full agent pipeline (no streaming) and persists everything
    in one transaction: the user's message, the assistant's reply, the
    query-execution audit trail, and citations."""
    history = _recent_history(db, conversation.tenant_id, conversation.id)

    user_message = Message(id=uuid.uuid4(), tenant_id=conversation.tenant_id, conversation_id=conversation.id, role="user", content=question)
    db.add(user_message)
    db.flush()

    graph = build_graph(db, user)
    final_state: AgentState = graph.invoke(_initial_state(conversation, user, question, history))

    return _persist_assistant_turn(db, conversation, final_state)


def stream_and_persist(db: Session, conversation: Conversation, user: User, question: str):
    """
    Generator used by the SSE endpoint. Yields (event_name, payload) tuples
    as each graph node completes, then persists the full turn once the
    graph finishes and yields a final "done" event with the saved message.
    Reuses the exact same compiled graph as the non-streaming path - there
    is no separate/duplicated orchestration logic for the streaming case.
    """
    history = _recent_history(db, conversation.tenant_id, conversation.id)

    user_message = Message(id=uuid.uuid4(), tenant_id=conversation.tenant_id, conversation_id=conversation.id, role="user", content=question)
    db.add(user_message)
    db.flush()

    graph = build_graph(db, user)
    state: AgentState = _initial_state(conversation, user, question, history)

    for chunk in graph.stream(state):
        for node_name, partial in chunk.items():
            state.update(partial)
            yield "stage", {"node": node_name, "intent": state.get("intent")}

    message = _persist_assistant_turn(db, conversation, state)
    yield "done", message


def _persist_assistant_turn(db: Session, conversation: Conversation, final_state: AgentState) -> Message:
    assistant_message = Message(
        id=uuid.uuid4(),
        tenant_id=conversation.tenant_id,
        conversation_id=conversation.id,
        role="assistant",
        content=final_state.get("final_answer", ""),
        detected_intent=final_state.get("intent"),
        model_name=final_state.get("model_name"),
        selected_sources={
            "connection_ids": [str(c) for c in final_state.get("active_connection_ids", [])],
            "knowledge_base_ids": [str(k) for k in final_state.get("active_knowledge_base_ids", [])],
        },
    )
    db.add(assistant_message)
    db.flush()

    for db_ev in final_state.get("database_evidence", []):
        query_execution = QueryExecution(
            id=uuid.uuid4(),
            tenant_id=conversation.tenant_id,
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            connection_id=uuid.UUID(db_ev["connection_id"]),
            generated_sql=db_ev["generated_sql"],
            normalized_sql=db_ev["normalized_sql"],
            validation_status=db_ev["validation_status"],
            validation_errors=db_ev["validation_errors"],
            referenced_tables=db_ev["referenced_tables"],
            execution_status=db_ev["execution_status"],
            returned_row_count=db_ev["row_count"],
            result_preview={"columns": db_ev["columns"], "rows": db_ev["rows"][:10]},
        )
        db.add(query_execution)
        db.flush()

        if db_ev["execution_status"] == "success":
            db.add(
                MessageCitation(
                    id=uuid.uuid4(),
                    tenant_id=conversation.tenant_id,
                    message_id=assistant_message.id,
                    citation_type="database",
                    query_execution_id=query_execution.id,
                    title=db_ev["connection_name"],
                    source_reference=", ".join(db_ev["referenced_tables"]),
                )
            )

    for doc_ev in final_state.get("document_evidence", []):
        db.add(
            MessageCitation(
                id=uuid.uuid4(),
                tenant_id=conversation.tenant_id,
                message_id=assistant_message.id,
                citation_type="document",
                file_id=uuid.UUID(doc_ev["file_id"]),
                chunk_id=uuid.UUID(doc_ev["chunk_id"]),
                title=doc_ev["file_name"],
                page_number=doc_ev["page_number"],
                relevance_score=doc_ev["similarity"],
            )
        )

    conversation.last_message_at = datetime.now(timezone.utc)
    if conversation.title is None:
        conversation.title = final_state.get("question", "New conversation")[:100]
    db.add(conversation)
    db.commit()
    db.refresh(assistant_message)
    return assistant_message
