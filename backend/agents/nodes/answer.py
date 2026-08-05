from agents.state import AgentState
from app.config import get_settings
from services.llm.client import ChatMessage, chat
from services.llm.prompts import ANSWER_SYSTEM_PROMPT, GENERAL_SYSTEM_PROMPT

settings = get_settings()

_MAX_ROWS_IN_PROMPT = 25


def answer_node(state: AgentState) -> dict:
    intent = state.get("intent", "general")

    if intent == "general":
        history = _history_messages(state)
        try:
            answer = chat(
                [ChatMessage(role="system", content=GENERAL_SYSTEM_PROMPT), *history, ChatMessage(role="user", content=state["question"])]
            )
        except Exception as exc:  # noqa: BLE001
            answer = f"Sorry, I couldn't reach the language model provider ({exc})."
        return {"final_answer": answer, "model_name": settings.groq_model}

    evidence_text = _build_evidence_text(state)
    if not evidence_text.strip():
        return {
            "final_answer": (
                "I couldn't find any accessible database results or relevant document excerpts to answer that. "
                "Try selecting a connection or knowledge base for this conversation, or rephrasing your question."
            ),
            "model_name": settings.groq_model,
        }

    system_prompt = ANSWER_SYSTEM_PROMPT.format(evidence=evidence_text)
    try:
        answer = chat([ChatMessage(role="system", content=system_prompt), ChatMessage(role="user", content=state["question"])])
    except Exception as exc:  # noqa: BLE001
        answer = f"Sorry, I couldn't reach the language model provider ({exc})."

    return {"final_answer": answer, "model_name": settings.groq_model}


def _history_messages(state: AgentState) -> list[ChatMessage]:
    history = state.get("conversation_history", [])[-6:]
    return [ChatMessage(role=h["role"], content=h["content"]) for h in history]


def _build_evidence_text(state: AgentState) -> str:
    parts = []

    for db_ev in state.get("database_evidence", []):
        if db_ev["validation_status"] == "blocked":
            parts.append(
                f"[Database: {db_ev['connection_name']}] The generated query was blocked by the security "
                f"validator and could not be run. Reasons: {'; '.join(db_ev['validation_errors'])}"
            )
            continue
        if db_ev["execution_status"] != "success":
            parts.append(f"[Database: {db_ev['connection_name']}] The query failed to execute against the database.")
            continue

        rows_preview = db_ev["rows"][:_MAX_ROWS_IN_PROMPT]
        parts.append(
            f"[Database: {db_ev['connection_name']}] Query result ({db_ev['row_count']} row(s), "
            f"showing up to {len(rows_preview)}): columns={db_ev['columns']} rows={rows_preview}"
        )

    for doc_ev in state.get("document_evidence", []):
        page_info = f", page {doc_ev['page_number']}" if doc_ev["page_number"] else ""
        parts.append(f"[Document: {doc_ev['file_name']}{page_info}] {doc_ev['content']}")

    return "\n\n".join(parts)
