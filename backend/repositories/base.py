import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """
    Every repository method that reads or writes tenant-owned data takes an
    explicit tenant_id and filters by it. This is the single most important
    rule in the whole codebase for the multi-tenancy guarantee: there is no
    code path in any repository that can return another tenant's rows.
    """

    model: type[ModelT]

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, tenant_id: uuid.UUID, record_id: uuid.UUID) -> ModelT | None:
        stmt = select(self.model).where(self.model.id == record_id, self.model.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def delete(self, instance: ModelT) -> None:
        self.db.delete(instance)
        self.db.flush()

    def add(self, instance: ModelT) -> ModelT:
        self.db.add(instance)
        self.db.flush()
        return instance
