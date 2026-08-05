import uuid

from sqlalchemy.orm import Session

from models.audit_log import AuditLog


def record_audit_event(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    status: str = "success",
    details: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            details=details or {},
        )
    )
    db.commit()
