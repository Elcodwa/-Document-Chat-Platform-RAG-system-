from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from schemas.common import ORMBase


class CreateConnectionRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    database_type: str = Field(pattern="^(postgresql|mysql)$")
    host: str = Field(min_length=1, max_length=255)
    port: int | None = None
    database_name: str = Field(min_length=1, max_length=255)
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=0, max_length=512)
    ssl_enabled: bool = False


class ConnectionResponse(ORMBase):
    id: UUID
    name: str
    database_type: str
    host: str | None
    port: int | None
    database_name: str | None
    username: str | None
    ssl_enabled: bool
    status: str
    last_tested_at: datetime | None
    last_test_message: str | None
    schema_sync_status: str
    last_schema_sync_at: datetime | None
    is_active: bool
    created_at: datetime


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    server_version: str | None = None


class SchemaSyncResponse(BaseModel):
    table_count: int
    column_count: int


class ColumnResponse(ORMBase):
    id: UUID
    column_name: str
    data_type: str
    is_primary_key: bool
    is_foreign_key: bool
    referenced_table: str | None
    referenced_column: str | None


class TableResponse(ORMBase):
    id: UUID
    schema_name: str
    table_name: str
    estimated_row_count: int | None
    is_enabled: bool
    columns: list[ColumnResponse] = []
