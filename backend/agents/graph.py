"""
Wires the individual agent nodes into a single graph.

The routing is intentionally a simple, fully sequential state machine
(no parallel fan-out/fan-in) - it's easy to reason about, easy to test
with a stubbed LLM, and covers all four intents:

    general:   classify -> answer
    database:  classify -> db_agent -> merge -> answer
    document:  classify -> rag_agent -> merge -> answer
    hybrid:    classify -> db_agent -> rag_agent -> merge -> answer
"""
import uuid

from langgraph.graph import StateGraph, START, END
from sqlalchemy.orm import Session

from agents.nodes.answer import answer_node
from agents.nodes.classify import classify_node
from agents.nodes.db_agent import make_db_agent_node
from agents.nodes.merge import merge_node
from agents.nodes.rag_agent import make_rag_agent_node
from agents.state import AgentState
from models.user import User


def build_graph(db: Session, user: User):
    graph = StateGraph(AgentState)
    graph.add_node("classify", classify_node)
    graph.add_node("db_agent", make_db_agent_node(db, user))
    graph.add_node("rag_agent", make_rag_agent_node(db))
    graph.add_node("merge", merge_node)
    graph.add_node("answer", answer_node)

    graph.add_edge(START, "classify")

    def route_after_classify(state: AgentState) -> str:
        intent = state.get("intent", "general")
        if intent in ("database", "hybrid"):
            return "db_agent"
        if intent == "document":
            return "rag_agent"
        return "answer"

    graph.add_conditional_edges(
        "classify", route_after_classify, {"db_agent": "db_agent", "rag_agent": "rag_agent", "answer": "answer"}
    )

    def route_after_db(state: AgentState) -> str:
        return "rag_agent" if state.get("intent") == "hybrid" else "merge"

    graph.add_conditional_edges("db_agent", route_after_db, {"rag_agent": "rag_agent", "merge": "merge"})

    graph.add_edge("rag_agent", "merge")
    graph.add_edge("merge", "answer")
    graph.add_edge("answer", END)

    return graph.compile()


def run_chat_pipeline(
    db: Session,
    user: User,
    *,
    tenant_id: uuid.UUID,
    question: str,
    conversation_history: list[dict],
    active_connection_ids: list[uuid.UUID],
    active_knowledge_base_ids: list[uuid.UUID],
) -> AgentState:
    compiled = build_graph(db, user)
    initial_state: AgentState = {
        "tenant_id": tenant_id,
        "user_id": user.id,
        "question": question,
        "conversation_history": conversation_history,
        "active_connection_ids": active_connection_ids,
        "active_knowledge_base_ids": active_knowledge_base_ids,
        "database_evidence": [],
        "document_evidence": [],
    }
    return compiled.invoke(initial_state)
