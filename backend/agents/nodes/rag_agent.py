from sqlalchemy.orm import Session

from agents.state import AgentState, DocumentEvidence
from repositories.file_repo import FileRepository
from services.documents.retrieval_service import retrieve_relevant_chunks


def make_rag_agent_node(db: Session):
    file_repo = FileRepository(db)

    def rag_agent_node(state: AgentState) -> dict:
        kb_ids = state.get("active_knowledge_base_ids", [])
        if not kb_ids:
            return {"document_evidence": []}

        results = retrieve_relevant_chunks(
            db,
            tenant_id=state["tenant_id"],
            knowledge_base_ids=kb_ids,
            query=state["question"],
        )

        evidence: list[DocumentEvidence] = []
        for r in results:
            file_record = file_repo.get_by_id(state["tenant_id"], r.chunk.file_id)
            evidence.append(
                DocumentEvidence(
                    file_id=str(r.chunk.file_id),
                    file_name=file_record.original_name if file_record else "Unknown file",
                    chunk_id=str(r.chunk.id),
                    page_number=r.chunk.page_number,
                    content=r.chunk.content,
                    similarity=round(r.similarity, 4),
                )
            )
        return {"document_evidence": evidence}

    return rag_agent_node
