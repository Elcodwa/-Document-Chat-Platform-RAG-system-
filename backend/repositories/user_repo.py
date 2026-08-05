import uuid

from sqlalchemy import select

from models.user import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, tenant_id: uuid.UUID, email: str) -> User | None:
        stmt = select(User).where(User.tenant_id == tenant_id, User.email == email.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id_any_tenant(self, user_id: uuid.UUID) -> User | None:
        """Used only by the auth dependency, right after decoding a JWT."""
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_tenant(self, tenant_id: uuid.UUID) -> list[User]:
        stmt = select(User).where(User.tenant_id == tenant_id).order_by(User.created_at)
        return list(self.db.execute(stmt).scalars().all())
