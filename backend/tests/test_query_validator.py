import uuid

import pytest

from models.database_schema import DatabaseTable
from services.database.permission_service import AccessibleTable
from services.database.query_validator import validate_and_prepare_sql


def _table(name: str, schema: str = "public") -> DatabaseTable:
    return DatabaseTable(id=uuid.uuid4(), schema_name=schema, table_name=name)


def _accessible(name: str, schema: str = "public", allowed_columns=None, row_filters=None) -> dict:
    return {
        (schema, name): AccessibleTable(
            table=_table(name, schema), allowed_columns=allowed_columns, row_filters=row_filters or []
        )
    }


DEFAULTS = dict(dialect="postgres", default_schema="public", max_rows=500, max_query_chars=4000)


class TestAllowsSafeQueries:
    def test_simple_select_is_allowed(self):
        result = validate_and_prepare_sql(
            "SELECT id, name FROM customers", accessible_tables=_accessible("customers"), **DEFAULTS
        )
        assert result.is_valid, result.errors
        assert "LIMIT" in result.normalized_sql
        assert result.referenced_tables == ["public.customers"]

    def test_join_across_two_accessible_tables(self):
        tables = {**_accessible("orders"), **_accessible("customers")}
        sql = "SELECT o.id, c.name FROM orders o JOIN customers c ON o.customer_id = c.id"
        result = validate_and_prepare_sql(sql, accessible_tables=tables, **DEFAULTS)
        assert result.is_valid, result.errors

    def test_cte_is_allowed(self):
        sql = "WITH recent AS (SELECT id FROM orders) SELECT * FROM recent"
        result = validate_and_prepare_sql(sql, accessible_tables=_accessible("orders"), **DEFAULTS)
        assert result.is_valid, result.errors

    def test_bare_explain_is_allowed(self):
        result = validate_and_prepare_sql(
            "EXPLAIN SELECT id FROM customers", accessible_tables=_accessible("customers"), **DEFAULTS
        )
        assert result.is_valid, result.errors
        assert result.normalized_sql.upper().startswith("EXPLAIN")


class TestBlocksWrites:
    @pytest.mark.parametrize(
        "sql",
        [
            "DROP TABLE customers",
            "DELETE FROM customers",
            "UPDATE customers SET name = 'x'",
            "INSERT INTO customers (name) VALUES ('x')",
            "ALTER TABLE customers ADD COLUMN x int",
            "TRUNCATE TABLE customers",
            "GRANT SELECT ON customers TO public",
        ],
    )
    def test_dml_and_ddl_rejected(self, sql):
        result = validate_and_prepare_sql(sql, accessible_tables=_accessible("customers"), **DEFAULTS)
        assert not result.is_valid

    def test_writable_cte_is_rejected(self):
        sql = "WITH deleted AS (DELETE FROM orders WHERE id = 1 RETURNING *) SELECT * FROM deleted"
        result = validate_and_prepare_sql(sql, accessible_tables=_accessible("orders"), **DEFAULTS)
        assert not result.is_valid

    def test_select_into_is_rejected(self):
        sql = "SELECT * INTO new_table FROM customers"
        result = validate_and_prepare_sql(sql, accessible_tables=_accessible("customers"), **DEFAULTS)
        assert not result.is_valid

    def test_explain_analyze_is_rejected(self):
        sql = "EXPLAIN ANALYZE SELECT * FROM customers"
        result = validate_and_prepare_sql(sql, accessible_tables=_accessible("customers"), **DEFAULTS)
        assert not result.is_valid


class TestBlocksInjectionAndEscape:
    def test_multiple_statements_rejected(self):
        sql = "SELECT 1; DROP TABLE customers"
        result = validate_and_prepare_sql(sql, accessible_tables=_accessible("customers"), **DEFAULTS)
        assert not result.is_valid

    def test_sql_comment_rejected(self):
        sql = "SELECT * FROM customers -- ; DROP TABLE customers"
        result = validate_and_prepare_sql(sql, accessible_tables=_accessible("customers"), **DEFAULTS)
        assert not result.is_valid

    def test_blocked_function_rejected(self):
        sql = "SELECT pg_sleep(5)"
        result = validate_and_prepare_sql(sql, accessible_tables=_accessible("customers"), **DEFAULTS)
        assert not result.is_valid

    def test_system_schema_rejected(self):
        sql = "SELECT * FROM pg_catalog.pg_user"
        result = validate_and_prepare_sql(sql, accessible_tables=_accessible("customers"), **DEFAULTS)
        assert not result.is_valid

    def test_table_not_in_allowlist_rejected(self):
        sql = "SELECT * FROM secret_table"
        result = validate_and_prepare_sql(sql, accessible_tables=_accessible("customers"), **DEFAULTS)
        assert not result.is_valid


class TestPermissionEnforcement:
    def test_column_restricted_table_blocks_disallowed_column(self):
        tables = _accessible("customers", allowed_columns={"id", "name"})
        sql = "SELECT id, name, ssn FROM customers"
        result = validate_and_prepare_sql(sql, accessible_tables=tables, **DEFAULTS)
        assert not result.is_valid

    def test_column_restricted_table_allows_permitted_columns(self):
        tables = _accessible("customers", allowed_columns={"id", "name"})
        sql = "SELECT id, name FROM customers"
        result = validate_and_prepare_sql(sql, accessible_tables=tables, **DEFAULTS)
        assert result.is_valid, result.errors

    def test_star_blocked_on_column_restricted_table(self):
        tables = _accessible("customers", allowed_columns={"id", "name"})
        sql = "SELECT * FROM customers"
        result = validate_and_prepare_sql(sql, accessible_tables=tables, **DEFAULTS)
        assert not result.is_valid

    def test_row_filter_is_injected(self):
        tables = _accessible("customers", row_filters=[{"column": "country", "value": "EG"}])
        sql = "SELECT id FROM customers"
        result = validate_and_prepare_sql(sql, accessible_tables=tables, **DEFAULTS)
        assert result.is_valid, result.errors
        assert "country" in result.normalized_sql and "EG" in result.normalized_sql

    def test_row_filter_injected_through_join(self):
        tables = {
            **_accessible("orders"),
            **_accessible("customers", row_filters=[{"column": "country", "value": "EG"}]),
        }
        sql = "SELECT o.id, c.name FROM orders o JOIN customers c ON o.customer_id = c.id"
        result = validate_and_prepare_sql(sql, accessible_tables=tables, **DEFAULTS)
        assert result.is_valid, result.errors
        assert "c.country" in result.normalized_sql.replace('"', "")

    def test_row_filter_cannot_be_bypassed_by_llm_supplied_where(self):
        """Even if the LLM's own WHERE clause is unrelated, our filter must
        still end up ANDed into the final query - never OR'd, never
        dropped."""
        tables = _accessible("customers", row_filters=[{"column": "country", "value": "EG"}])
        sql = "SELECT id FROM customers WHERE active = true"
        result = validate_and_prepare_sql(sql, accessible_tables=tables, **DEFAULTS)
        assert result.is_valid
        normalized = result.normalized_sql.upper()
        assert "AND" in normalized
        assert "COUNTRY" in normalized


class TestRowLimit:
    def test_limit_is_added_when_missing(self):
        result = validate_and_prepare_sql(
            "SELECT id FROM customers", accessible_tables=_accessible("customers"), dialect="postgres",
            default_schema="public", max_rows=100, max_query_chars=4000,
        )
        assert result.is_valid
        assert "LIMIT 100" in result.normalized_sql

    def test_limit_is_capped_when_too_large(self):
        result = validate_and_prepare_sql(
            "SELECT id FROM customers LIMIT 999999", accessible_tables=_accessible("customers"),
            dialect="postgres", default_schema="public", max_rows=100, max_query_chars=4000,
        )
        assert result.is_valid
        assert "LIMIT 100" in result.normalized_sql

    def test_limit_below_cap_is_preserved(self):
        result = validate_and_prepare_sql(
            "SELECT id FROM customers LIMIT 10", accessible_tables=_accessible("customers"),
            dialect="postgres", default_schema="public", max_rows=100, max_query_chars=4000,
        )
        assert result.is_valid
        assert "LIMIT 10" in result.normalized_sql
