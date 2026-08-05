import os
import uuid

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from core.tenant_context import get_current_user
from db.session import get_db
from models.file import File
from models.user import User
from repositories.file_repo import FileRepository
from repositories.kb_repo import KnowledgeBaseRepository
from schemas.knowledge_base import FileResponse
from services.audit_service import record_audit_event
from services.documents.upload_service import process_file, save_upload_to_disk

router = APIRouter(prefix="/api/knowledge-bases/{kb_id}/files", tags=["files"])


@router.get("", response_model=list[FileResponse])
def list_files(kb_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    kb = KnowledgeBaseRepository(db).get_by_id(user.tenant_id, kb_id)
    if kb is None:
        raise NotFoundError("Knowledge base not found.")
    return FileRepository(db).list_for_knowledge_base(user.tenant_id, kb_id)


@router.post("", response_model=FileResponse, status_code=201)
async def upload_file(
    kb_id: uuid.UUID, file: UploadFile, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    kb = KnowledgeBaseRepository(db).get_by_id(user.tenant_id, kb_id)
    if kb is None:
        raise NotFoundError("Knowledge base not found.")

    content = await file.read()
    stored_name, absolute_path, checksum = save_upload_to_disk(user.tenant_id, file.filename, content)
    extension = os.path.splitext(file.filename)[1].lower()

    file_record = File(
        id=uuid.uuid4(),
        tenant_id=user.tenant_id,
        knowledge_base_id=kb_id,
        uploaded_by=user.id,
        original_name=file.filename,
        stored_name=stored_name,
        storage_path=absolute_path,
        mime_type=file.content_type,
        extension=extension,
        file_size_bytes=len(content),
        checksum=checksum,
        processing_status="pending",
    )
    db.add(file_record)
    db.commit()

    record_audit_event(
        db, tenant_id=user.tenant_id, user_id=user.id, action="file.uploaded",
        resource_type="file", resource_id=str(file_record.id), details={"original_name": file.filename},
    )

    # Runs synchronously and inline for this project's scope - see
    # ARCHITECTURE.md for why, and how you'd swap in a background worker.
    process_file(db, file_record)
    db.refresh(file_record)
    return file_record


@router.delete("/{file_id}", status_code=204)
def delete_file(kb_id: uuid.UUID, file_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file_repo = FileRepository(db)
    file_record = file_repo.get_by_id(user.tenant_id, file_id)
    if file_record is None or file_record.knowledge_base_id != kb_id:
        raise NotFoundError("File not found.")

    try:
        if os.path.exists(file_record.storage_path):
            os.remove(file_record.storage_path)
    except OSError:
        pass

    file_repo.delete(file_record)
    db.commit()
    record_audit_event(
        db, tenant_id=user.tenant_id, user_id=user.id, action="file.deleted", resource_type="file", resource_id=str(file_id)
    )
