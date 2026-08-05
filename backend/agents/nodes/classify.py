from agents.state import AgentState
from app.logging_config import get_logger
from services.llm.client import ChatMessage, chat
from services.llm.prompts import CLASSIFY_SYSTEM_PROMPT

logger = get_logger(__name__)

_VALID_INTENTS = {"database", "document", "hybrid", "general"}


def classify_node(state: AgentState) -> dict:
    has_connections = bool(state.get("active_connection_ids"))
    has_knowledge_bases = bool(state.get("active_knowledge_base_ids"))

    if not has_connections and not has_knowledge_bases:
        return {"intent": "general"}

    if has_connections and not has_knowledge_bases:
        allowed = {"database", "general"}
        default = "database"
    elif has_knowledge_bases and not has_connections:
        allowed = {"document", "general"}
        default = "document"
    else:
        allowed = _VALID_INTENTS
        default = "hybrid"

    try:
        raw = chat(
            [
                ChatMessage(role="system", content=CLASSIFY_SYSTEM_PROMPT),
                ChatMessage(role="user", content=state["question"]),
            ],
            temperature=0,
        )
        candidate = raw.strip().lower().split()[0].strip(".:,!\"'") if raw.strip() else ""
    except Exception:  # noqa: BLE001 - classification failure should never crash the whole chat
        logger.warning("Intent classification failed, falling back to default.", exc_info=True)
        candidate = ""

    intent = candidate if candidate in allowed else default
    return {"intent": intent}
