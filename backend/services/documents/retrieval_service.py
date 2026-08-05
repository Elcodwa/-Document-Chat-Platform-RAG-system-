import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.document_chunk import DocumentChunk
from services.documents.embedding_service import embed_query


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    similarity: float  # 1 - cosine_distance, so higher is more similar


def retrieve_relevant_chunks(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    knowledge_base_ids: list[uuid.UUID],
    query: str,
    top_k: int = 6,
    min_similarity: float = 0.2,
) -> list[RetrievedChunk]:
    """
    Embeds the user's question and finds the most similar chunks, scoped
    strictly to this tenant and to only the knowledge bases the
    conversation has explicitly selected - a knowledge base attached to
    another tenant, or one the user didn't pick for this chat, is never
    reachable here regardless of how similar its content might be.
    """
    if not knowledge_base_ids:
        return []

    query_vector = embed_query(query)
    distance = DocumentChunk.embedding.cosine_distance(query_vector)

    stmt = (
        select(DocumentChunk, distance.label("distance"))
        .where(
            DocumentChunk.tenant_id == tenant_id,
            DocumentChunk.knowledge_base_id.in_(knowledge_base_ids),
            DocumentChunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(top_k)
    )

    results = []
    for chunk, dist in db.execute(stmt).all():
        similarity = 1 - float(dist)
        if similarity >= min_similarity:
            results.append(RetrievedChunk(chunk=chunk, similarity=similarity))
    return results
