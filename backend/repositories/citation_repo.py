import uuid

from sqlalchemy import select

from models.citation import MessageCitation
from repositories.base import BaseRepository


class CitationRepository(BaseRepository[MessageCitation]):
    model = MessageCitation

    def list_for_message(self, tenant_id: uuid.UUID, message_id: uuid.UUID) -> list[MessageCitation]:
        stmt = select(MessageCitation).where(
            MessageCitation.tenant_id == tenant_id, MessageCitation.message_id == message_id
        )
        return list(self.db.execute(stmt).scalars().all())
