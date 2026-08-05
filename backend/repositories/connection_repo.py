import uuid

from sqlalchemy import select

from models.database_connection import DatabaseConnection
from repositories.base import BaseRepository


class ConnectionRepository(BaseRepository[DatabaseConnection]):
    model = DatabaseConnection

    def list_for_tenant(self, tenant_id: uuid.UUID) -> list[DatabaseConnection]:
        stmt = (
            select(DatabaseConnection)
            .where(DatabaseConnection.tenant_id == tenant_id)
            .order_by(DatabaseConnection.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_name(self, tenant_id: uuid.UUID, name: str) -> DatabaseConnection | None:
        stmt = select(DatabaseConnection).where(
            DatabaseConnection.tenant_id == tenant_id, DatabaseConnection.name == name
        )
        return self.db.execute(stmt).scalar_one_or_none()
