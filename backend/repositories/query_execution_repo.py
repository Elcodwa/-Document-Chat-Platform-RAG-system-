import uuid

from sqlalchemy import select

from models.query_execution import QueryExecution
from repositories.base import BaseRepository


class QueryExecutionRepository(BaseRepository[QueryExecution]):
    model = QueryExecution

    def get_for_message(self, tenant_id: uuid.UUID, message_id: uuid.UUID) -> QueryExecution | None:
        stmt = select(QueryExecution).where(
            QueryExecution.tenant_id == tenant_id, QueryExecution.message_id == message_id
        )
        return self.db.execute(stmt).scalar_one_or_none()
