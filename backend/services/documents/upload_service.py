import hashlib
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.exceptions import FileProcessingError
from app.logging_config import get_logger
from models.document_chunk import DocumentChunk
from models.file import File
from services.documents.chunking_service import chunk_pages
from services.documents.embedding_service import embed_texts
from services.documents.parsers import SUPPORTED_EXTENSIONS, extract_text

logger = get_logger(__name__)
settings = get_settings()


def save_upload_to_disk(tenant_id: uuid.UUID, original_name: str, content: bytes) -> tuple[str, str, str]:
    """Returns (stored_name, absolute_path, checksum)."""
    extension = os.path.splitext(original_name)[1].lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise FileProcessingError(
            f"Unsupported file type '{extension}'. Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise FileProcessingError(f"File exceeds the maximum allowed size of {settings.max_upload_size_mb}MB.")

    tenant_dir = os.path.join(settings.storage_path, str(tenant_id))
    os.makedirs(tenant_dir, exist_ok=True)

    stored_name = f"{uuid.uuid4()}{extension}"
    absolute_path = os.path.join(tenant_dir, stored_name)
    with open(absolute_path, "wb") as f:
        f.write(content)

    checksum = hashlib.sha256(content).hexdigest()
    return stored_name, absolute_path, checksum


def process_file(db: Session, file_record: File) -> None:
    """
    Runs the full pipeline synchronously: extract -> chunk -> embed ->
    persist. For the scope of this project this runs inline right after
    upload (simple, predictable, no extra moving parts); a production
    deployment handling large files or high upload volume would move this
    into a background worker queue instead - see ARCHITECTURE.md.
    """
    try:
        file_record.processing_status = "processing"
        db.add(file_record)
        db.commit()

        extension = file_record.extension or os.path.splitext(file_record.original_name)[1].lower()
        extracted = extract_text(file_record.storage_path, extension)

        pages = [(p.page_number, p.text) for p in extracted.pages]
        chunks = chunk_pages(
            pages,
            chunk_size_tokens=settings.chunk_size_tokens,
            chunk_overlap_tokens=settings.chunk_overlap_tokens,
        )

        if not chunks:
            raise FileProcessingError("No extractable text was found in this file.")

        embeddings = embed_texts([c.content for c in chunks])

        for chunk, vector in zip(chunks, embeddings):
            db.add(
                DocumentChunk(
                    id=uuid.uuid4(),
                    tenant_id=file_record.tenant_id,
                    knowledge_base_id=file_record.knowledge_base_id,
                    file_id=file_record.id,
                    chunk_index=chunk.index,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    token_count=len(chunk.content) // 4,
                    embedding=vector,
                )
            )

        file_record.processing_status = "completed"
        file_record.page_count = extracted.page_count
        file_record.extracted_text_length = len(extracted.full_text)
        file_record.processed_at = datetime.now(timezone.utc)
        file_record.processing_error = None
        db.add(file_record)
        db.commit()

    except FileProcessingError as exc:
        db.rollback()
        file_record.processing_status = "failed"
        file_record.processing_error = exc.public_message
        db.add(file_record)
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error processing file_id=%s", file_record.id)
        db.rollback()
        file_record.processing_status = "failed"
        file_record.processing_error = "An unexpected error occurred while processing this file."
        db.add(file_record)
        db.commit()
