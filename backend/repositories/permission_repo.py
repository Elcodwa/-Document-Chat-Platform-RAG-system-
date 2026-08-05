import uuid

from sqlalchemy import select

from models.permission import TablePermission
from models.role import UserRole
from repositories.base import BaseRepository


class PermissionRepository(BaseRepository[TablePermission]):
    model = TablePermission

    def list_role_ids_for_user(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        stmt = select(UserRole.role_id).where(UserRole.user_id == user_id)
        return [row[0] for row in self.db.execute(stmt).all()]

    def list_permissions_for_connection(
        self, tenant_id: uuid.UUID, connection_id: uuid.UUID, user_id: uuid.UUID, role_ids: list[uuid.UUID]
    ) -> list[TablePermission]:
        """
        All permission rows that apply to this user, either directly
        (user_id match) or through one of their roles (role_id match).
        """
        stmt = select(TablePermission).where(
            TablePermission.tenant_id == tenant_id,
            TablePermission.connection_id == connection_id,
            (TablePermission.user_id == user_id) | (TablePermission.role_id.in_(role_ids or [uuid.uuid4()])),
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_for_table(self, tenant_id: uuid.UUID, table_id: uuid.UUID) -> list[TablePermission]:
        stmt = select(TablePermission).where(
            TablePermission.tenant_id == tenant_id, TablePermission.table_id == table_id
        )
        return list(self.db.execute(stmt).scalars().all())
