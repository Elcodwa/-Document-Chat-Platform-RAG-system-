import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class DatabaseConnection(Base):
    """
    A tenant-owned pointer to a *live* customer database. We never copy the
    customer's business data into this application database - only enough
    connection metadata to open a controlled, read-only session at query
    time. See services/database/engine_factory.py.
    """

    __tablename__ = "database_connections"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_database_connection_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    database_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "postgresql" | "mysql"
    host: Mapped[str | None] = mapped_column(String(255))
    port: Mapped[int | None] = mapped_column(Integer)
    database_name: Mapped[str | None] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255))

    # Credentials are always encrypted at rest (core/encryption.py). Never
    # store or log the plaintext password anywhere.
    encrypted_password: Mapped[str | None] = mapped_column(Text)

    ssl_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    connection_options: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_test_message: Mapped[str | None] = mapped_column(Text)

    schema_sync_status: Mapped[str] = mapped_column(String(30), default="pending")
    last_schema_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tables: Mapped[list["DatabaseTable"]] = relationship(back_populates="connection", cascade="all, delete-orphan")
