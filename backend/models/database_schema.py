import uuid
from datetime import datetime

from sqlalchemy import String, Integer, BigInteger, Boolean, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class DatabaseTable(Base):
    """
    Cached metadata about one table discovered on a live connection. This is
    what the Text-to-SQL agent is actually shown - never the live database's
    full information_schema, and never more than what permissions allow.
    """

    __tablename__ = "database_tables"
    __table_args__ = (UniqueConstraint("connection_id", "schema_name", "table_name", name="uq_database_table"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("database_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    schema_name: Mapped[str] = mapped_column(String(255), nullable=False, default="public")
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    table_type: Mapped[str] = mapped_column(String(50), nullable=False, default="table")
    description: Mapped[str | None] = mapped_column(Text)
    estimated_row_count: Mapped[int | None] = mapped_column(BigInteger)
    primary_key_columns: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    connection: Mapped["DatabaseConnection"] = relationship(back_populates="tables")
    columns: Mapped[list["DatabaseColumn"]] = relationship(back_populates="table", cascade="all, delete-orphan")


class DatabaseColumn(Base):
    __tablename__ = "database_columns"
    __table_args__ = (UniqueConstraint("table_id", "column_name", name="uq_database_column"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("database_tables.id", ondelete="CASCADE"), nullable=False, index=True
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(100), nullable=False)
    ordinal_position: Mapped[int | None] = mapped_column(Integer)
    is_nullable: Mapped[bool | None] = mapped_column(Boolean)
    is_primary_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_foreign_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    referenced_table: Mapped[str | None] = mapped_column(String(255))
    referenced_column: Mapped[str | None] = mapped_column(String(255))
    sample_values: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    table: Mapped["DatabaseTable"] = relationship(back_populates="columns")
