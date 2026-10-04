"""Page-aware document processing: PDF text extraction / OCR → document_pages with quality signals."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy.orm import Session

from app.models import Document, DocumentPage
from app.models.enums import ActorType, AuditEvent, DocumentKind, ExtractionMethod, ProcessingStatus
from app.safety.text_quality import FLAG_OCR_UNAVAILABLE, page_quality
from app.services import audit
from app.services.ocr import OcrEngine
from app.storage.base import StorageBackend

logger = logging.getLogger("carelynx.processing")

MIN_PAGE_TEXT_CHARS = 20


@dataclass
class ExtractedPage:
    page_number: int
    text: str | None
    method: ExtractionMethod
    ocr_confidence: float | None = None
    extra_flags: tuple[str, ...] = ()


def _extract_pdf(data: bytes) -> list[ExtractedPage]:
    reader = PdfReader(io.BytesIO(data))
    pages: list[ExtractedPage] = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if len(text) >= MIN_PAGE_TEXT_CHARS:
            pages.append(ExtractedPage(i, text, ExtractionMethod.PDF_TEXT))
        else:
            # Scanned page inside a PDF. Rasterising requires poppler/pdfium which is not part of the MVP
            # stack; flag explicitly rather than drop silently.
            pages.append(ExtractedPage(i, text or None, ExtractionMethod.OCR_UNAVAILABLE, None, (FLAG_OCR_UNAVAILABLE,)))
    return pages


def _extract_image(data: bytes, ocr: OcrEngine) -> list[ExtractedPage]:
    if not ocr.available:
        return [ExtractedPage(1, None, ExtractionMethod.OCR_UNAVAILABLE, None, (FLAG_OCR_UNAVAILABLE,))]
    result = ocr.recognize(data)
    return [ExtractedPage(1, result.text.strip() or None, ExtractionMethod.OCR, result.confidence)]


def classify(text: str) -> DocumentKind:
    upper = text.upper()
    if "DISCHARGE SUMMARY" in upper:
        return DocumentKind.DISCHARGE_SUMMARY
    if "PRESCRIPTION" in upper or "\nRX\n" in f"\n{upper}\n":
        return DocumentKind.PRESCRIPTION
    if "APPOINTMENT" in upper or "FOLLOW-UP" in upper[:200]:
        return DocumentKind.FOLLOW_UP
    return DocumentKind.UNKNOWN


def process_document(db: Session, storage: StorageBackend, doc: Document, ocr: OcrEngine) -> Document:
    doc.processing_status = ProcessingStatus.PROCESSING
    doc.error_code = None
    audit.record(db, AuditEvent.DOCUMENT_PROCESSING_STARTED, case_id=doc.case_id, document_id=doc.id)
    db.commit()

    try:
        data = storage.get(doc.storage_key)
        if doc.mime_type == "application/pdf":
            extracted = _extract_pdf(data)
        else:
            extracted = _extract_image(data, ocr)
    except (PdfReadError, ValueError, OSError) as exc:
        logger.warning("Processing failed document_id=%s err=%s", doc.id, type(exc).__name__)
        doc.processing_status = ProcessingStatus.FAILED
        doc.error_code = "PDF_PARSE_ERROR" if isinstance(exc, PdfReadError) else "READ_ERROR"
        audit.record(
            db, AuditEvent.DOCUMENT_PROCESSING_FAILED, case_id=doc.case_id, document_id=doc.id,
            error_code=doc.error_code,
        )
        db.commit()
        return doc

    # Re-processing replaces page rows.
    for p in list(doc.pages):
        db.delete(p)
    db.flush()

    warnings = False
    full_text: list[str] = []
    for ep in extracted:
        q = page_quality(ep.text)
        flags = list(dict.fromkeys([*ep.extra_flags, *q.flags]))
        quality = q.score
        if ep.ocr_confidence is not None:
            quality = min(quality, ep.ocr_confidence)
        if flags:
            warnings = True
        doc.pages.append(
            DocumentPage(
                page_number=ep.page_number,
                text=ep.text,
                ocr_confidence=ep.ocr_confidence,
                extraction_method=ep.method,
                text_quality=quality,
                quality_flags=flags,
            )
        )
        if ep.text:
            full_text.append(ep.text)

    doc.page_count = len(extracted)
    doc.document_kind = classify("\n".join(full_text))
    doc.processing_status = ProcessingStatus.PROCESSED_WITH_WARNINGS if warnings else ProcessingStatus.PROCESSED
    audit.record(
        db,
        AuditEvent.DOCUMENT_PROCESSED,
        actor_type=ActorType.SYSTEM,
        case_id=doc.case_id,
        document_id=doc.id,
        page_count=doc.page_count,
        status=doc.processing_status.value,
        kind=doc.document_kind.value,
    )
    db.commit()
    return doc
