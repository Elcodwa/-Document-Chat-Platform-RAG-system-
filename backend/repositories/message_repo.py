import uuid

from sqlalchemy import select

from models.message import Message
from repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    model = Message

    def list_for_conversation(self, tenant_id: uuid.UUID, conversation_id: uuid.UUID) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.tenant_id == tenant_id, Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())
