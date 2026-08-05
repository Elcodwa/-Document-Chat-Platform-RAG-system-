"""
Permission resolution.

Default posture (deliberately simple, and documented here rather than
buried in code): a tenant admin can read every table that has been synced
and enabled for a connection. A regular member can read nothing on a
connection until a table_permissions row grants them (or one of their
roles) access - at which point column_permissions and row_filter further
narrow what they see.

If multiple applicable grants define different row filters for the same
table, we combine them with AND (the more restrictive, safer choice).
The same logic does NOT apply to column grants: a column is readable if
ANY applicable grant allows it (most permissive for columns, most
restrictive for rows) - because row filters encode "which customers' data"
(narrower is safer), while column grants encode "which fields you were
explicitly given" (union across your roles is the intuitive access model).
"""
import uuid
from dataclasses import dataclass, field

from models.database_schema import DatabaseTable
from models.user import User
from repositories.permission_repo import PermissionRepository
from repositories.schema_repo import SchemaRepository


@dataclass
class AccessibleTable:
    table: DatabaseTable
    allowed_columns: set[str] | None  # None == all columns allowed
    row_filters: list[dict] = field(default_factory=list)


class PermissionService:
    def __init__(self, db):
        self.db = db
        self.schema_repo = SchemaRepository(db)
        self.permission_repo = PermissionRepository(db)

    def get_accessible_tables(
        self, tenant_id: uuid.UUID, connection_id: uuid.UUID, user: User
    ) -> list[AccessibleTable]:
        all_tables = [
            t
            for t in self.schema_repo.list_tables_for_connection(tenant_id, connection_id)
            if t.is_enabled
        ]

        if user.is_tenant_admin:
            return [AccessibleTable(table=t, allowed_columns=None, row_filters=[]) for t in all_tables]

        role_ids = self.permission_repo.list_role_ids_for_user(user.id)
        grants = self.permission_repo.list_permissions_for_connection(tenant_id, connection_id, user.id, role_ids)

        grants_by_table: dict[uuid.UUID, list] = {}
        for grant in grants:
            if grant.can_read:
                grants_by_table.setdefault(grant.table_id, []).append(grant)

        accessible: list[AccessibleTable] = []
        for table in all_tables:
            table_grants = grants_by_table.get(table.id)
            if not table_grants:
                continue

            row_filters: list[dict] = [g.row_filter for g in table_grants if g.row_filter]

            # If NO grant for this table defines any column_permissions rows,
            # the grant is "whole table" -> all columns allowed. Otherwise,
            # a column is allowed if any grant's column_permissions marks it
            # readable.
            any_grant_has_explicit_columns = any(g.column_permissions for g in table_grants)
            allowed_columns: set[str] | None = None

            if any_grant_has_explicit_columns:
                columns_by_id = {c.id: c.column_name for c in self.schema_repo.list_columns(tenant_id, table.id)}
                allowed_columns = set()
                for grant in table_grants:
                    if not grant.column_permissions:
                        # This particular grant doesn't restrict columns ->
                        # it contributes every column of the table.
                        allowed_columns |= set(columns_by_id.values())
                        continue
                    for cp in grant.column_permissions:
                        if cp.can_read:
                            col_name = columns_by_id.get(cp.column_id)
                            if col_name:
                                allowed_columns.add(col_name)

            accessible.append(AccessibleTable(table=table, allowed_columns=allowed_columns, row_filters=row_filters))

        return accessible

    def get_accessible_table_by_name(
        self,
        tenant_id: uuid.UUID,
        connection_id: uuid.UUID,
        user: User,
        schema_name: str,
        table_name: str,
    ) -> AccessibleTable | None:
        for entry in self.get_accessible_tables(tenant_id, connection_id, user):
            if entry.table.schema_name == schema_name and entry.table.table_name == table_name:
                return entry
        return None
