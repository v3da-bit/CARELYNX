"""Document endpoints: upload, metadata, page text (for evidence viewer), original file."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.security import Role, current_role
from app.db.session import get_db
from app.models import DocumentPage
from app.models.enums import ActorType, AuditEvent
from app.schemas.document import DocumentOut, DocumentUploadResponse, PageDetail, ProcessResponse
from app.services import audit, pipeline
from app.services import documents as doc_service
from app.services.ocr import get_ocr_engine
from app.storage.base import StorageBackend
from app.storage.local import get_storage

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    case_id: uuid.UUID | None = Form(default=None),
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
) -> DocumentUploadResponse:
    max_bytes = get_settings().max_upload_bytes
    data = await file.read(max_bytes + 1)  # bounded read
    doc = doc_service.upload_document(
        db, storage, data=data, filename=file.filename, max_bytes=max_bytes, case_id=case_id
    )
    return DocumentUploadResponse(
        id=doc.id, case_id=doc.case_id, filename=doc.filename, status=doc.processing_status
    )


@router.post("/{document_id}/process", response_model=ProcessResponse)
async def process_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
) -> ProcessResponse:
    """Runs processing → extraction → evidence → safety synchronously; returns the resulting status."""
    doc = doc_service.get_document(db, document_id)
    doc = await pipeline.run_document(db, storage, doc, ocr=get_ocr_engine())
    return ProcessResponse(document_id=doc.id, status=doc.processing_status)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> DocumentOut:
    return DocumentOut.model_validate(doc_service.get_document(db, document_id))


@router.get("/{document_id}/pages/{page_number}", response_model=PageDetail)
def get_page(document_id: uuid.UUID, page_number: int, db: Session = Depends(get_db)) -> PageDetail:
    page = (
        db.query(DocumentPage)
        .filter(DocumentPage.document_id == document_id, DocumentPage.page_number == page_number)
        .one_or_none()
    )
    if page is None:
        raise AppError(ErrorCode.NOT_FOUND, "Page not found.", 404)
    return PageDetail.model_validate(page)


@router.get("/{document_id}/file")
def get_original_file(
    document_id: uuid.UUID,
    role: Role = Depends(current_role),
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
) -> Response:
    """Authorized, audited, non-cacheable access to the original. No public/signed URL is ever exposed."""
    doc = doc_service.get_document(db, document_id)
    audit.record(
        db,
        AuditEvent.DOCUMENT_ACCESSED,
        actor_type=ActorType.REVIEWER if role is Role.REVIEWER else ActorType.PATIENT,
        case_id=doc.case_id,
        document_id=doc.id,
    )
    db.commit()
    return Response(
        content=storage.get(doc.storage_key),
        media_type=doc.mime_type,
        headers={"Content-Disposition": "inline", "Cache-Control": "no-store, private"},
    )
