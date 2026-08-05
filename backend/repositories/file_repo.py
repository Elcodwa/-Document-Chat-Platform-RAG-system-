import uuid

from sqlalchemy import select

from models.file import File
from repositories.base import BaseRepository


class FileRepository(BaseRepository[File]):
    model = File

    def list_for_knowledge_base(self, tenant_id: uuid.UUID, knowledge_base_id: uuid.UUID) -> list[File]:
        stmt = (
            select(File)
            .where(File.tenant_id == tenant_id, File.knowledge_base_id == knowledge_base_id)
            .order_by(File.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_for_tenant(self, tenant_id: uuid.UUID) -> list[File]:
        stmt = select(File).where(File.tenant_id == tenant_id).order_by(File.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())
