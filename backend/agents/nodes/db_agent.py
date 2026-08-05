"""
The Text-to-SQL agent node.

Design note: this node only *reads* (connections, cached schema,
permissions) and calls the LLM/validator/executor - it never writes to
the application database. Persisting the audit trail (QueryExecution rows)
happens once, in the calling service, after the whole graph finishes and
we have a real message_id to attach everything to. This keeps the agent
layer side-effect-free and easy to unit test with a fake LLM.
"""
import uuid

from sqlalchemy.orm import Session

from agents.state import AgentState, DatabaseEvidence
from app.config import get_settings
from app.logging_config import get_logger
from models.user import User
from repositories.connection_repo import ConnectionRepository
from services.database.permission_service import PermissionService
from services.database.query_executor import execute_validated_sql
from services.database.query_validator import validate_and_prepare_sql
from services.llm.client import ChatMessage, chat
from services.llm.prompts import SQL_GENERATION_SYSTEM_PROMPT, SQL_REPAIR_SYSTEM_PROMPT

logger = get_logger(__name__)
settings = get_settings()

_MAX_TABLES_IN_PROMPT = 25
_MAX_COLUMNS_PER_TABLE_IN_PROMPT = 30


def make_db_agent_node(db: Session, user: User):
    connection_repo = ConnectionRepository(db)
    permission_service = PermissionService(db)

    def db_agent_node(state: AgentState) -> dict:
        evidence: list[DatabaseEvidence] = []
        tenant_id = state["tenant_id"]

        for connection_id in state.get("active_connection_ids", []):
            connection = connection_repo.get_by_id(tenant_id, connection_id)
            if connection is None or not connection.is_active:
                continue

            accessible = permission_service.get_accessible_tables(tenant_id, connection.id, user)
            if not accessible:
                continue

            dialect = "postgres" if connection.database_type == "postgresql" else "mysql"
            default_schema = "public" if connection.database_type == "postgresql" else (connection.database_name or "")
            accessible_map = {(a.table.schema_name.lower(), a.table.table_name.lower()): a for a in accessible}
            schema_description = _describe_schema(accessible)

            raw_sql = _generate_sql(state["question"], dialect, schema_description)
            result = validate_and_prepare_sql(
                raw_sql,
                dialect=dialect,
                default_schema=default_schema,
                accessible_tables=accessible_map,
                max_rows=settings.sql_max_rows,
                max_query_chars=settings.sql_max_query_chars,
            )

            if not result.is_valid:
                repaired_sql = _repair_sql(state["question"], raw_sql, result.errors, dialect, schema_description)
                if repaired_sql:
                    repaired_result = validate_and_prepare_sql(
                        repaired_sql,
                        dialect=dialect,
                        default_schema=default_schema,
                        accessible_tables=accessible_map,
                        max_rows=settings.sql_max_rows,
                        max_query_chars=settings.sql_max_query_chars,
                    )
                    if repaired_result.is_valid:
                        raw_sql, result = repaired_sql, repaired_result

            if not result.is_valid:
                evidence.append(
                    DatabaseEvidence(
                        connection_id=str(connection.id),
                        connection_name=connection.name,
                        generated_sql=raw_sql,
                        normalized_sql=None,
                        validation_status="blocked",
                        validation_errors=result.errors,
                        execution_status=None,
                        columns=[],
                        rows=[],
                        row_count=0,
                        referenced_tables=[],
                    )
                )
                continue

            exec_result = execute_validated_sql(connection, result.normalized_sql, max_rows=settings.sql_max_rows)
            evidence.append(
                DatabaseEvidence(
                    connection_id=str(connection.id),
                    connection_name=connection.name,
                    generated_sql=raw_sql,
                    normalized_sql=result.normalized_sql,
                    validation_status="passed",
                    validation_errors=[],
                    execution_status="success" if exec_result.success else "error",
                    columns=exec_result.columns,
                    rows=exec_result.rows,
                    row_count=exec_result.row_count,
                    referenced_tables=result.referenced_tables,
                )
            )

        return {"database_evidence": evidence}

    return db_agent_node


def _describe_schema(accessible) -> str:
    lines = []
    for entry in accessible[:_MAX_TABLES_IN_PROMPT]:
        table = entry.table
        columns = table.columns or []
        if entry.allowed_columns is not None:
            columns = [c for c in columns if c.column_name in entry.allowed_columns]
        columns = columns[:_MAX_COLUMNS_PER_TABLE_IN_PROMPT]
        col_desc = ", ".join(f"{c.column_name} {c.data_type}" for c in columns)
        lines.append(f"- {table.schema_name}.{table.table_name}({col_desc})")
    return "\n".join(lines) if lines else "(no tables available)"


def _generate_sql(question: str, dialect: str, schema_description: str) -> str:
    system_prompt = SQL_GENERATION_SYSTEM_PROMPT.format(dialect=dialect, schema_description=schema_description)
    try:
        raw = chat([ChatMessage(role="system", content=system_prompt), ChatMessage(role="user", content=question)])
        return _strip_code_fences(raw)
    except Exception:  # noqa: BLE001
        logger.warning("SQL generation failed.", exc_info=True)
        return ""


def _repair_sql(question: str, previous_sql: str, errors: list[str], dialect: str, schema_description: str) -> str | None:
    prompt = SQL_REPAIR_SYSTEM_PROMPT.format(
        question=question,
        previous_sql=previous_sql,
        errors="\n".join(errors),
        schema_description=schema_description,
    )
    try:
        raw = chat([ChatMessage(role="system", content=prompt)])
        return _strip_code_fences(raw)
    except Exception:  # noqa: BLE001
        logger.warning("SQL repair attempt failed.", exc_info=True)
        return None


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()
