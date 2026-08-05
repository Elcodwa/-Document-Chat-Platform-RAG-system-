import uuid

from sqlalchemy import select

from models.knowledge_base import KnowledgeBase
from repositories.base import BaseRepository


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    model = KnowledgeBase

    def list_for_tenant(self, tenant_id: uuid.UUID) -> list[KnowledgeBase]:
        stmt = (
            select(KnowledgeBase)
            .where(KnowledgeBase.tenant_id == tenant_id)
            .order_by(KnowledgeBase.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
