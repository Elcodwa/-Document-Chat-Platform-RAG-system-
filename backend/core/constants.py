"""
Security constants for the Text-to-SQL safety layer.

These lists are the enforceable, testable expression of the "Mandatory SQL
Security Controls" from the platform spec. They are intentionally kept as
plain data (not scattered through business logic) so they can be unit
tested directly - see tests/test_query_validator.py.
"""

# Only these top-level statement kinds are ever allowed to reach a live
# customer database. Everything else (INSERT, UPDATE, DELETE, DDL, GRANT,
# COPY, ...) is rejected before it is executed.
ALLOWED_STATEMENT_KEYS = {"select"}

# EXPLAIN is allowed by the spec, but ONLY the plan - never EXPLAIN ANALYZE,
# which actually *executes* the underlying statement (including any writes
# hidden inside a writable CTE). We special-case this in the validator.
EXPLAIN_ANALYZE_PATTERN = r"\bANALY[SZ]E\b"

# System / administrative schemas that must never be queried, regardless of
# permissions - these expose server internals, other tenants' catalog data,
# or platform credentials.
BLOCKED_SCHEMAS = {
    "pg_catalog",
    "information_schema",
    "pg_toast",
    "mysql",
    "sys",
    "performance_schema",
}

# Functions that can read files, sleep, open network connections, or
# otherwise escape the "read some rows" contract of a chat query.
BLOCKED_FUNCTIONS = {
    "pg_sleep",
    "pg_read_file",
    "pg_read_binary_file",
    "pg_ls_dir",
    "pg_stat_file",
    "lo_import",
    "lo_export",
    "dblink",
    "dblink_connect",
    "load_file",
    "sleep",
    "benchmark",
    "xp_cmdshell",
}

# Statement-level AST node types that indicate a write or schema change is
# hiding somewhere in the query (most commonly inside a "writable CTE" like
# `WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x`).
WRITE_NODE_TYPES = (
    "Insert",
    "Update",
    "Delete",
    "Create",
    "Drop",
    "Alter",
    "TruncateTable",
    "Grant",
    "Command",
)

DEFAULT_MAX_ROWS = 500
DEFAULT_STATEMENT_TIMEOUT_SECONDS = 10
DEFAULT_MASK_TOKEN = "•••MASKED•••"
