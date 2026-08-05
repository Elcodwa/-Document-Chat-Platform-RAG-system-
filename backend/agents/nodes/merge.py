from agents.state import AgentState


def merge_node(state: AgentState) -> dict:
    """
    A deliberately thin node. Its job is just to guarantee both evidence
    lists exist in state (a single-source query never populates the other
    list), so the answer node doesn't need defensive .get() calls
    everywhere. Kept as its own graph step - rather than folded into
    answer_node - because it's the natural place to add cross-source
    ranking/deduplication later without touching answer generation.
    """
    return {
        "database_evidence": state.get("database_evidence", []),
        "document_evidence": state.get("document_evidence", []),
    }
