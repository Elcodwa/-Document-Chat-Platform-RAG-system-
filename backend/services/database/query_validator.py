"""
The SQL security validator.

Every piece of SQL text the LLM produces passes through
`validate_and_prepare_sql` before it is ever sent to a customer's database.
Nothing downstream trusts the LLM's output directly - not the statement
type, not the tables it claims to touch, not its row limit. This module
parses the SQL into a real AST (via sqlglot) and only allows it through if
every check below passes; the SQL that finally gets executed is always a
re-serialized version of the *validated* AST, never the LLM's original
text, which closes the gap between "what we checked" and "what runs".

Checks performed, in order:
  1. Length limit (guards against pathological input).
  2. EXPLAIN handling: EXPLAIN ANALYZE is rejected outright because it
     executes the underlying statement (a well-known way to smuggle a
     write through what looks like a read-only diagnostic command).
  3. Raw comment markers are rejected before parsing (defense in depth).
  4. Must parse as exactly one statement.
  5. Must be a SELECT (optionally with CTEs) - not INSERT/UPDATE/DELETE/
     DDL/GRANT/anything else.
  6. No SELECT INTO (creates a table as a side effect).
  7. No write/DDL node anywhere in the tree - catches "writable CTEs" like
     `WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x`, which still
     parse with a top-level key of "select".
  8. No blocked functions (pg_sleep, dblink, load_file, xp_cmdshell, ...).
  9. Every referenced table must be in the caller-supplied allowlist of
     tables this user can access on this connection; system schemas
     (pg_catalog, information_schema, mysql, ...) are always blocked.
  10. Column-level checks for tables with restricted column grants
      (best-effort: fully qualified columns and single-table queries are
      always checked; unqualified columns in multi-table joins are a
      documented limitation - see ARCHITECTURE.md).
  11. Row-level filters are injected directly into the WHERE clause of
      the scope where each filtered table is referenced (works through
      joins, subqueries, and CTEs) - the LLM never sees this filter and
      cannot remove or alter it, because it is added *after* generation.
  12. A LIMIT is enforced (added if missing, capped if too large).
"""
import re
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

from core.constants import (
    ALLOWED_STATEMENT_KEYS,
    BLOCKED_FUNCTIONS,
    BLOCKED_SCHEMAS,
    EXPLAIN_ANALYZE_PATTERN,
)
from services.database.permission_service import AccessibleTable

_WRITE_NODE_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.TruncateTable,
    exp.Grant,
    exp.Command,
    exp.Merge,
)

_COMMENT_PATTERN = re.compile(r"(--|/\*|\*/|#)")


@dataclass
class ValidationResult:
    is_valid: bool
    normalized_sql: str | None
    errors: list[str] = field(default_factory=list)
    referenced_tables: list[str] = field(default_factory=list)
    is_explain: bool = False


def validate_and_prepare_sql(
    raw_sql: str,
    *,
    dialect: str,
    default_schema: str,
    accessible_tables: dict[tuple[str, str], AccessibleTable],
    max_rows: int,
    max_query_chars: int = 4000,
) -> ValidationResult:
    sql = (raw_sql or "").strip()
    if not sql:
        return ValidationResult(False, None, ["The generated SQL was empty."])
    if len(sql) > max_query_chars:
        return ValidationResult(False, None, [f"Query exceeds the maximum allowed length ({max_query_chars} characters)."])

    sql = sql.rstrip().rstrip(";").strip()

    is_explain = False
    explain_match = re.match(r"^\s*EXPLAIN\b(.*)$", sql, re.IGNORECASE | re.DOTALL)
    if explain_match:
        remainder = explain_match.group(1).strip()
        if re.search(EXPLAIN_ANALYZE_PATTERN, remainder, re.IGNORECASE):
            return ValidationResult(
                False, None, ["EXPLAIN ANALYZE is blocked because it executes the underlying query; use plain EXPLAIN."]
            )
        if remainder.startswith("("):
            return ValidationResult(False, None, ["EXPLAIN options are not supported; use plain 'EXPLAIN <query>'."])
        is_explain = True
        sql = remainder

    if _COMMENT_PATTERN.search(sql):
        return ValidationResult(False, None, ["SQL comments are not allowed in generated queries."])

    try:
        statements = [s for s in sqlglot.parse(sql, read=dialect) if s is not None]
    except Exception as exc:  # noqa: BLE001
        return ValidationResult(False, None, [f"The SQL could not be parsed: {exc}"])

    if len(statements) == 0:
        return ValidationResult(False, None, ["The SQL could not be parsed."])
    if len(statements) > 1:
        return ValidationResult(False, None, ["Only a single SQL statement is allowed per request."])

    tree = statements[0]

    if tree.key not in ALLOWED_STATEMENT_KEYS:
        return ValidationResult(
            False, None, [f"Statement type '{tree.key}' is not allowed - only SELECT queries are permitted."]
        )

    if tree.args.get("into"):
        return ValidationResult(False, None, ["SELECT INTO is not allowed because it creates/writes a table."])

    write_nodes = list(tree.find_all(_WRITE_NODE_TYPES))
    if write_nodes:
        return ValidationResult(
            False, None, ["A write or schema-changing operation was found inside the query and has been blocked."]
        )

    blocked_functions_found = {
        fn.this.lower() for fn in tree.find_all(exp.Anonymous) if isinstance(fn.this, str) and fn.this.lower() in BLOCKED_FUNCTIONS
    }
    if blocked_functions_found:
        return ValidationResult(False, None, [f"Use of function(s) {sorted(blocked_functions_found)} is not allowed."])

    cte_names = _cte_names(tree)
    referenced_tables_out: set[str] = set()

    for select_node in tree.find_all(exp.Select):
        base_refs = [
            (table_node, alias)
            for table_node, alias in _base_table_refs(select_node)
            if not (table_node.db == "" and table_node.name.lower() in cte_names)
        ]
        alias_to_entry: dict[str, AccessibleTable] = {}

        for table_node, alias in base_refs:
            schema_name = (table_node.db or default_schema).lower()
            table_name = table_node.name.lower()

            if schema_name in BLOCKED_SCHEMAS:
                return ValidationResult(False, None, [f"Access to schema '{schema_name}' is not allowed."])

            entry = accessible_tables.get((schema_name, table_name))
            if entry is None:
                return ValidationResult(
                    False, None, [f"Table '{table_node.name}' is not accessible with your current permissions."]
                )
            alias_to_entry[alias] = entry
            referenced_tables_out.add(f"{schema_name}.{table_name}")

        single_entry = alias_to_entry[base_refs[0][1]] if len(base_refs) == 1 else None

        # --- star ("SELECT *" / "alias.*") checks ---
        for star in select_node.find_all(exp.Star):
            if isinstance(star.parent, exp.Column) and star.parent.table:
                entry = alias_to_entry.get(star.parent.table)
                if entry and entry.allowed_columns is not None:
                    return ValidationResult(
                        False,
                        None,
                        [f"'{star.parent.table}.*' is blocked: access to that table is column-restricted. Select explicit columns."],
                    )
            elif isinstance(star.parent, exp.Select):
                if single_entry is not None and single_entry.allowed_columns is not None:
                    return ValidationResult(
                        False, None, ["'SELECT *' is blocked: your access is column-restricted. Select explicit columns."]
                    )
                if single_entry is None and any(e.allowed_columns is not None for e in alias_to_entry.values()):
                    return ValidationResult(
                        False,
                        None,
                        ["'SELECT *' is blocked across a join where at least one table is column-restricted. Select explicit columns."],
                    )

        # --- named column checks (best-effort for ambiguous unqualified columns
        #     in multi-table queries - see ARCHITECTURE.md) ---
        for col in select_node.find_all(exp.Column):
            if isinstance(col.this, exp.Star):
                continue
            entry = alias_to_entry.get(col.table) if col.table else single_entry
            if entry is None:
                continue
            if entry.allowed_columns is not None and col.name.lower() not in {c.lower() for c in entry.allowed_columns}:
                return ValidationResult(
                    False, None, [f"Column '{col.name}' is not accessible with your current permissions."]
                )

        # --- row-level filter injection ---
        for table_node, alias in base_refs:
            entry = alias_to_entry.get(alias)
            if not entry or not entry.row_filters:
                continue
            for row_filter in entry.row_filters:
                column = row_filter.get("column")
                value = row_filter.get("value")
                if not column or value is None:
                    continue
                condition = sqlglot.condition(f"{alias}.{column} = {_literal_sql(value)}", dialect=dialect)
                select_node.where(condition, copy=False)

    existing_limit = tree.args.get("limit")
    current_limit_value = None
    if existing_limit is not None:
        try:
            current_limit_value = int(existing_limit.expression.this)
        except (AttributeError, ValueError, TypeError):
            current_limit_value = None

    final_tree = tree
    if current_limit_value is None or current_limit_value > max_rows:
        final_tree = tree.limit(max_rows)

    normalized_sql = final_tree.sql(dialect=dialect)
    if is_explain:
        normalized_sql = f"EXPLAIN {normalized_sql}"

    return ValidationResult(
        is_valid=True,
        normalized_sql=normalized_sql,
        errors=[],
        referenced_tables=sorted(referenced_tables_out),
        is_explain=is_explain,
    )


def _cte_names(tree: exp.Expression) -> set[str]:
    with_clause = tree.args.get("with")
    if not with_clause:
        return set()
    return {cte.alias.lower() for cte in with_clause.expressions if cte.alias}


def _base_table_refs(select_node: exp.Select) -> list[tuple[exp.Table, str]]:
    """Direct FROM/JOIN table references of this SELECT only - not tables
    inside nested subqueries, which are visited separately because they
    are their own exp.Select nodes."""
    refs: list[tuple[exp.Table, str]] = []
    from_clause = select_node.args.get("from")
    if from_clause is not None and isinstance(from_clause.this, exp.Table):
        refs.append((from_clause.this, from_clause.this.alias_or_name))
    for join in select_node.args.get("joins") or []:
        if isinstance(join.this, exp.Table):
            refs.append((join.this, join.this.alias_or_name))
    return refs


def _literal_sql(value) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"
