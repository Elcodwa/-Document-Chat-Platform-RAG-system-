import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from core.encryption import encrypt_value
from core.tenant_context import get_current_user, require_tenant_admin
from db.session import get_db
from models.database_connection import DatabaseConnection
from models.user import User
from repositories.connection_repo import ConnectionRepository
from repositories.schema_repo import SchemaRepository
from schemas.connections import (
    ConnectionResponse,
    ConnectionTestResponse,
    CreateConnectionRequest,
    SchemaSyncResponse,
    TableResponse,
)
from services.audit_service import record_audit_event
from services.database.connection_tester import test_connection
from services.database.engine_factory import SUPPORTED_DATABASE_TYPES
from services.database.schema_discovery import sync_schema

router = APIRouter(prefix="/api/connections", tags=["connections"])


@router.get("", response_model=list[ConnectionResponse])
def list_connections(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ConnectionRepository(db).list_for_tenant(user.tenant_id)


@router.post("", response_model=ConnectionResponse, status_code=201)
def create_connection(
    payload: CreateConnectionRequest, user: User = Depends(require_tenant_admin), db: Session = Depends(get_db)
):
    connection = DatabaseConnection(
        id=uuid.uuid4(),
        tenant_id=user.tenant_id,
        created_by=user.id,
        name=payload.name,
        database_type=payload.database_type,
        host=payload.host,
        port=payload.port,
        database_name=payload.database_name,
        username=payload.username,
        encrypted_password=encrypt_value(payload.password),
        ssl_enabled=payload.ssl_enabled,
    )
    db.add(connection)
    db.commit()
    record_audit_event(
        db, tenant_id=user.tenant_id, user_id=user.id, action="connection.created",
        resource_type="database_connection", resource_id=str(connection.id),
    )
    return connection


@router.get("/{connection_id}", response_model=ConnectionResponse)
def get_connection(connection_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connection = ConnectionRepository(db).get_by_id(user.tenant_id, connection_id)
    if connection is None:
        raise NotFoundError("Connection not found.")
    return connection


@router.post("/{connection_id}/test", response_model=ConnectionTestResponse)
def test_connection_endpoint(
    connection_id: uuid.UUID, user: User = Depends(require_tenant_admin), db: Session = Depends(get_db)
):
    connection = ConnectionRepository(db).get_by_id(user.tenant_id, connection_id)
    if connection is None:
        raise NotFoundError("Connection not found.")

    result = test_connection(connection)

    connection.last_tested_at = datetime.now(timezone.utc)
    connection.last_test_message = result.message
    connection.status = "connected" if result.success else "error"
    db.add(connection)
    db.commit()

    record_audit_event(
        db, tenant_id=user.tenant_id, user_id=user.id, action="connection.tested",
        resource_type="database_connection", resource_id=str(connection.id),
        status="success" if result.success else "failure",
    )
    return ConnectionTestResponse(success=result.success, message=result.message, server_version=result.server_version)


@router.post("/{connection_id}/sync-schema", response_model=SchemaSyncResponse)
def sync_schema_endpoint(
    connection_id: uuid.UUID, user: User = Depends(require_tenant_admin), db: Session = Depends(get_db)
):
    connection = ConnectionRepository(db).get_by_id(user.tenant_id, connection_id)
    if connection is None:
        raise NotFoundError("Connection not found.")

    result = sync_schema(db, connection)

    connection.schema_sync_status = "completed"
    connection.last_schema_sync_at = datetime.now(timezone.utc)
    db.add(connection)
    db.commit()

    record_audit_event(
        db, tenant_id=user.tenant_id, user_id=user.id, action="connection.schema_synced",
        resource_type="database_connection", resource_id=str(connection.id),
        details={"table_count": result.table_count, "column_count": result.column_count},
    )
    return SchemaSyncResponse(table_count=result.table_count, column_count=result.column_count)


@router.get("/{connection_id}/tables", response_model=list[TableResponse])
def list_tables(connection_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connection = ConnectionRepository(db).get_by_id(user.tenant_id, connection_id)
    if connection is None:
        raise NotFoundError("Connection not found.")
    return SchemaRepository(db).list_tables_for_connection(user.tenant_id, connection_id)


@router.get("/meta/supported-types", response_model=list[str])
def supported_types():
    return list(SUPPORTED_DATABASE_TYPES)
