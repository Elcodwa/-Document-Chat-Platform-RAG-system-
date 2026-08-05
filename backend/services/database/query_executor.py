"""
Executes an already-validated, already-normalized SQL string against a
tenant's live database. This module trusts its input completely - it is
only ever called with the `normalized_sql` that came out of
query_validator.validate_and_prepare_sql, never with raw LLM output.
"""
import time
from dataclasses import dataclass, field

from sqlalchemy import text

from app.config import get_settings
from app.exceptions import SQLExecutionError
from app.logging_config import get_logger
from models.database_connection import DatabaseConnection
from services.database.engine_factory import build_engine

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class ExecutionResult:
    success: bool
    columns: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: int = 0
    error_message: str | None = None


def execute_validated_sql(connection: DatabaseConnection, normalized_sql: str, *, max_rows: int) -> ExecutionResult:
    engine = None
    started = time.perf_counter()
    try:
        engine = build_engine(connection, statement_timeout_seconds=settings.sql_statement_timeout_seconds)
        with engine.connect() as conn:
            # A read-only transaction is an extra safety net beyond the
            # validator: even if something slipped through validation, the
            # database driver itself will refuse to perform a write here
            # (this is enforced server-side by Postgres; MySQL's session
            # is additionally kept to a single, short-lived SELECT).
            if connection.database_type == "postgresql":
                conn.execute(text("SET TRANSACTION READ ONLY"))

            cursor_result = conn.execute(text(normalized_sql))
            columns = list(cursor_result.keys())
            fetched = cursor_result.fetchmany(max_rows)
            rows = [dict(zip(columns, row)) for row in fetched]

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return ExecutionResult(
            success=True, columns=columns, rows=rows, row_count=len(rows), execution_time_ms=elapsed_ms
        )
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.warning("Query execution failed for connection_id=%s: %s", connection.id, exc)
        return ExecutionResult(
            success=False,
            execution_time_ms=elapsed_ms,
            error_message="The query could not be executed against the target database.",
        )
    finally:
        if engine is not None:
            engine.dispose()


def execute_validated_sql_or_raise(connection: DatabaseConnection, normalized_sql: str, *, max_rows: int) -> ExecutionResult:
    result = execute_validated_sql(connection, normalized_sql, max_rows=max_rows)
    if not result.success:
        raise SQLExecutionError(result.error_message or "Query execution failed.")
    return result
