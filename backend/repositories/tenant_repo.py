from sqlalchemy import select

from models.tenant import Tenant
from repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    model = Tenant

    def get_by_code(self, code: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.code == code)
        return self.db.execute(stmt).scalar_one_or_none()
