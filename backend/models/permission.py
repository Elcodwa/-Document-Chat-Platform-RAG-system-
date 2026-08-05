import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, String, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class TablePermission(Base):
    """
    Grants a role OR a specific user access to one table on one connection,
    optionally scoped to a row filter (e.g. {"column": "region", "value":
    "EG"}). Exactly one of role_id / user_id must be set - never both,
    never neither (enforced at the DB level with a CHECK constraint, and
    again in services/database/permission_service.py).
    """

    __tablename__ = "table_permissions"
    __table_args__ = (
        CheckConstraint(
            "(role_id IS NOT NULL AND user_id IS NULL) OR (role_id IS NULL AND user_id IS NOT NULL)",
            name="chk_permission_subject",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("database_connections.id", ondelete="CASCADE"), nullable=False
    )
    table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("database_tables.id", ondelete="CASCADE"), nullable=False
    )

    can_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    can_insert: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_update: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # e.g. {"column": "region", "value": "EG"} -> every query against this
    # table gets "AND region = 'EG'" injected by the query executor. The LLM
    # never sees this filter and cannot alter it (see query_validator.py).
    row_filter: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    column_permissions: Mapped[list["ColumnPermission"]] = relationship(
        back_populates="table_permission", cascade="all, delete-orphan"
    )


class ColumnPermission(Base):
    __tablename__ = "column_permissions"
    __table_args__ = (
        UniqueConstraint("table_permission_id", "column_id", name="uq_column_permission"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("table_permissions.id", ondelete="CASCADE"), nullable=False
    )
    column_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("database_columns.id", ondelete="CASCADE"), nullable=False
    )
    can_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    can_filter: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mask_type: Mapped[str | None] = mapped_column(String(50), default=None)  # e.g. "full", "partial"

    table_permission: Mapped["TablePermission"] = relationship(back_populates="column_permissions")
