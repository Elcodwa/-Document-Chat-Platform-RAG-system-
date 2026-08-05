import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from core.tenant_context import get_current_user
from db.session import get_db
from models.knowledge_base import KnowledgeBase
from models.user import User
from repositories.file_repo import FileRepository
from repositories.kb_repo import KnowledgeBaseRepository
from schemas.knowledge_base import CreateKnowledgeBaseRequest, KnowledgeBaseResponse
from services.audit_service import record_audit_event

router = APIRouter(prefix="/api/knowledge-bases", tags=["knowledge-bases"])


@router.get("", response_model=list[KnowledgeBaseResponse])
def list_knowledge_bases(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = KnowledgeBaseRepository(db)
    file_repo = FileRepository(db)
    kbs = repo.list_for_tenant(user.tenant_id)
    results = []
    for kb in kbs:
        response = KnowledgeBaseResponse.model_validate(kb)
        response.file_count = len(file_repo.list_for_knowledge_base(user.tenant_id, kb.id))
        results.append(response)
    return results


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
def create_knowledge_base(
    payload: CreateKnowledgeBaseRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    kb = KnowledgeBase(
        id=uuid.uuid4(), tenant_id=user.tenant_id, created_by=user.id, name=payload.name, description=payload.description
    )
    db.add(kb)
    db.commit()
    record_audit_event(
        db, tenant_id=user.tenant_id, user_id=user.id, action="knowledge_base.created",
        resource_type="knowledge_base", resource_id=str(kb.id),
    )
    return KnowledgeBaseResponse.model_validate(kb)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(kb_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    kb = KnowledgeBaseRepository(db).get_by_id(user.tenant_id, kb_id)
    if kb is None:
        raise NotFoundError("Knowledge base not found.")
    response = KnowledgeBaseResponse.model_validate(kb)
    response.file_count = len(FileRepository(db).list_for_knowledge_base(user.tenant_id, kb_id))
    return response
