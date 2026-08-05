import uuid

from sqlalchemy import select, delete

from models.database_schema import DatabaseTable, DatabaseColumn
from repositories.base import BaseRepository


class SchemaRepository(BaseRepository[DatabaseTable]):
    model = DatabaseTable

    def list_tables_for_connection(self, tenant_id: uuid.UUID, connection_id: uuid.UUID) -> list[DatabaseTable]:
        stmt = (
            select(DatabaseTable)
            .where(DatabaseTable.tenant_id == tenant_id, DatabaseTable.connection_id == connection_id)
            .order_by(DatabaseTable.schema_name, DatabaseTable.table_name)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_table(
        self, tenant_id: uuid.UUID, connection_id: uuid.UUID, schema_name: str, table_name: str
    ) -> DatabaseTable | None:
        stmt = select(DatabaseTable).where(
            DatabaseTable.tenant_id == tenant_id,
            DatabaseTable.connection_id == connection_id,
            DatabaseTable.schema_name == schema_name,
            DatabaseTable.table_name == table_name,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def clear_for_connection(self, tenant_id: uuid.UUID, connection_id: uuid.UUID) -> None:
        stmt = delete(DatabaseTable).where(
            DatabaseTable.tenant_id == tenant_id, DatabaseTable.connection_id == connection_id
        )
        self.db.execute(stmt)
        self.db.flush()

    def list_columns(self, tenant_id: uuid.UUID, table_id: uuid.UUID) -> list[DatabaseColumn]:
        stmt = (
            select(DatabaseColumn)
            .where(DatabaseColumn.tenant_id == tenant_id, DatabaseColumn.table_id == table_id)
            .order_by(DatabaseColumn.ordinal_position)
        )
        return list(self.db.execute(stmt).scalars().all())
