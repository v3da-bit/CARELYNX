"""Orchestrates the document pipeline. Each stage lives in its own service; this module only sequences them."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.models import Document
from app.models.enums import ProcessingStatus
from app.services.ocr import OcrEngine
from app.services.processing import process_document
from app.storage.base import StorageBackend


async def run_document(db: Session, storage: StorageBackend, doc: Document, *, ocr: OcrEngine) -> Document:
    if doc.processing_status == ProcessingStatus.PROCESSING:
        raise AppError(ErrorCode.INVALID_STATE, "Document is already being processed.", 409)
    doc = process_document(db, storage, doc, ocr)
    
    from app.services.extraction import extract_facts
    await extract_facts(db, doc)
    
    return doc
