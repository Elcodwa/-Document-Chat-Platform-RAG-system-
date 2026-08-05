"""
Turns a stored DatabaseConnection row into a live, short-lived SQLAlchemy
engine. This is deliberately separate from the application's own database
engine (db/session.py) - business data from a customer's database must
never be persisted into our metadata store, and every engine created here
is used for exactly one request and then disposed.
"""
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from core.encryption import decrypt_value
from models.database_connection import DatabaseConnection

_DRIVERS = {
    "postgresql": "postgresql+psycopg",
    "mysql": "mysql+pymysql",
}

DEFAULT_PORTS = {"postgresql": 5432, "mysql": 3306}

SUPPORTED_DATABASE_TYPES = tuple(_DRIVERS.keys())


def build_connection_url(connection: DatabaseConnection, *, password_override: str | None = None) -> str:
    if connection.database_type not in _DRIVERS:
        raise ValueError(f"Unsupported database_type: {connection.database_type}")

    driver = _DRIVERS[connection.database_type]
    password = password_override if password_override is not None else decrypt_value(connection.encrypted_password or "")
    port = connection.port or DEFAULT_PORTS[connection.database_type]

    user = quote_plus(connection.username or "")
    pwd = quote_plus(password or "")
    host = connection.host or "localhost"
    db_name = connection.database_name or ""

    return f"{driver}://{user}:{pwd}@{host}:{port}/{db_name}"


def build_engine(connection: DatabaseConnection, *, statement_timeout_seconds: int = 10) -> Engine:
    """
    Build a fresh, read-only-intentioned engine for one connection.

    We keep pool size at 1 with no overflow: this is a short-lived engine
    used for a single query, not a long-running pool shared across
    requests, so we don't want it silently holding many idle sockets open
    on the customer's database.
    """
    url = build_connection_url(connection)

    connect_args: dict = {}
    if connection.database_type == "postgresql":
        # options="-c statement_timeout=<ms>" enforces a hard server-side
        # timeout regardless of what the client does.
        connect_args["options"] = f"-c statement_timeout={statement_timeout_seconds * 1000}"
    elif connection.database_type == "mysql":
        connect_args["read_timeout"] = statement_timeout_seconds
        connect_args["connect_timeout"] = 5

    return create_engine(
        url,
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=True,
        connect_args=connect_args,
        future=True,
    )
