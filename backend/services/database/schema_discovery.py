"""
Schema discovery: connects to a tenant's live database, reflects its
tables/columns via SQLAlchemy's Inspector, and caches the result into our
own database_tables / database_columns tables.

Why cache instead of introspecting live on every chat message? Two
reasons: (1) it's what actually gets shown to the LLM and checked against
permissions - the agent is never handed a raw information_schema dump of
someone's production database, and (2) it means a single "Sync schema"
click is a predictable, on-demand action rather than a query-time surprise.
"""
import uuid
from dataclasses import dataclass

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from core.constants import BLOCKED_SCHEMAS
from models.database_connection import DatabaseConnection
from models.database_schema import DatabaseTable, DatabaseColumn
from repositories.schema_repo import SchemaRepository
from services.database.engine_factory import build_engine


@dataclass
class SchemaSyncResult:
    table_count: int
    column_count: int


def sync_schema(db: Session, connection: DatabaseConnection) -> SchemaSyncResult:
    repo = SchemaRepository(db)
    engine = build_engine(connection, statement_timeout_seconds=15)
    try:
        inspector = inspect(engine)
        row_counts = _approximate_row_counts(engine, connection.database_type)

        # Wipe and re-insert. Simpler and safer than diffing, and this is a
        # deliberate, infrequent admin action rather than a hot path.
        repo.clear_for_connection(connection.tenant_id, connection.id)

        schema_names = _usable_schema_names(inspector, connection.database_type)
        table_count = 0
        column_count = 0

        for schema_name in schema_names:
            for table_name in inspector.get_table_names(schema=schema_name):
                pk_constraint = inspector.get_pk_constraint(table_name, schema=schema_name)
                pk_columns = pk_constraint.get("constrained_columns") or []
                fk_list = inspector.get_foreign_keys(table_name, schema=schema_name)
                fk_map = _build_fk_map(fk_list)

                table = DatabaseTable(
                    id=uuid.uuid4(),
                    tenant_id=connection.tenant_id,
                    connection_id=connection.id,
                    schema_name=schema_name,
                    table_name=table_name,
                    table_type="table",
                    primary_key_columns=pk_columns,
                    estimated_row_count=row_counts.get((schema_name, table_name)),
                    is_enabled=True,
                )
                db.add(table)
                db.flush()
                table_count += 1

                for position, col in enumerate(inspector.get_columns(table_name, schema=schema_name), start=1):
                    fk_target = fk_map.get(col["name"])
                    column = DatabaseColumn(
                        id=uuid.uuid4(),
                        tenant_id=connection.tenant_id,
                        table_id=table.id,
                        column_name=col["name"],
                        data_type=str(col.get("type")),
                        ordinal_position=position,
                        is_nullable=col.get("nullable"),
                        is_primary_key=col["name"] in pk_columns,
                        is_foreign_key=fk_target is not None,
                        referenced_table=fk_target[0] if fk_target else None,
                        referenced_column=fk_target[1] if fk_target else None,
                    )
                    db.add(column)
                    column_count += 1

        db.commit()
        return SchemaSyncResult(table_count=table_count, column_count=column_count)
    finally:
        engine.dispose()


def _usable_schema_names(inspector, database_type: str) -> list[str]:
    if database_type == "mysql":
        # In MySQL, the "database" IS the schema - just use the one we
        # connected to, via the inspector's default schema.
        default_schema = inspector.default_schema_name
        return [default_schema] if default_schema else []

    names = inspector.get_schema_names()
    return [n for n in names if n not in BLOCKED_SCHEMAS]


def _build_fk_map(fk_list: list[dict]) -> dict[str, tuple[str, str]]:
    """Maps local column name -> (referenced_table, referenced_column)."""
    mapping: dict[str, tuple[str, str]] = {}
    for fk in fk_list:
        referred_table = fk.get("referred_table")
        constrained = fk.get("constrained_columns") or []
        referred = fk.get("referred_columns") or []
        for local_col, remote_col in zip(constrained, referred):
            mapping[local_col] = (referred_table, remote_col)
    return mapping


def _approximate_row_counts(engine, database_type: str) -> dict[tuple[str, str], int]:
    """
    Fast, approximate row counts from database statistics - never a live
    COUNT(*), which could be slow or expensive on a large production table
    just to populate a metadata cache.
    """
    counts: dict[tuple[str, str], int] = {}
    try:
        with engine.connect() as conn:
            if database_type == "postgresql":
                rows = conn.execute(
                    text(
                        """
                        SELECT schemaname, relname, n_live_tup
                        FROM pg_stat_user_tables
                        """
                    )
                ).all()
                for schema_name, table_name, n_live_tup in rows:
                    counts[(schema_name, table_name)] = int(n_live_tup or 0)
            elif database_type == "mysql":
                rows = conn.execute(
                    text(
                        """
                        SELECT table_schema, table_name, table_rows
                        FROM information_schema.tables
                        WHERE table_schema = DATABASE()
                        """
                    )
                ).all()
                for schema_name, table_name, table_rows in rows:
                    counts[(schema_name, table_name)] = int(table_rows or 0)
    except Exception:  # noqa: BLE001 - row counts are a nice-to-have, never fatal
        pass
    return counts
