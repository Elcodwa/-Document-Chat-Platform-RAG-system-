from dataclasses import dataclass

from sqlalchemy import text

from app.exceptions import DatabaseConnectionError
from app.logging_config import get_logger
from models.database_connection import DatabaseConnection
from services.database.engine_factory import build_engine

logger = get_logger(__name__)


@dataclass
class ConnectionTestResult:
    success: bool
    message: str
    server_version: str | None = None


def test_connection(connection: DatabaseConnection) -> ConnectionTestResult:
    """
    Opens a real connection, runs a trivial query, and immediately closes
    it. Any failure is logged in full server-side (for the operator) but
    returned to the client as a short, generic message - the raw driver
    error can otherwise contain the host, database name, or even fragments
    of the connection string.
    """
    engine = None
    try:
        engine = build_engine(connection, statement_timeout_seconds=5)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            version = _server_version(conn, connection.database_type)
        return ConnectionTestResult(success=True, message="Connection successful.", server_version=version)
    except Exception as exc:  # noqa: BLE001 - intentionally broad, we never expose the raw error
        logger.warning("Connection test failed for connection_id=%s: %s", connection.id, exc)
        return ConnectionTestResult(
            success=False,
            message="Could not connect with the provided credentials. Check host, port, and password.",
        )
    finally:
        if engine is not None:
            engine.dispose()


def test_connection_or_raise(connection: DatabaseConnection) -> ConnectionTestResult:
    result = test_connection(connection)
    if not result.success:
        raise DatabaseConnectionError(result.message)
    return result


def _server_version(conn, database_type: str) -> str | None:
    try:
        if database_type == "postgresql":
            return conn.execute(text("SHOW server_version")).scalar()
        if database_type == "mysql":
            return conn.execute(text("SELECT VERSION()")).scalar()
    except Exception:  # noqa: BLE001
        return None
    return None
