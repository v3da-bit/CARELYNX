"""Orchestrates the document pipeline. Each stage lives in its own service; this module only sequences them.

State rules (API_CONTRACTS.md §4): only UPLOADED or FAILED documents may be processed (else 409). A FAILED
document's previous facts are removed first. Any stage failure leaves the document FAILED (never PROCESSING)
with a PROCESSING_FAILED review; only inference/provider failures surface as 502 MODEL_ERROR.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.ai.provider import ProviderError
from app.core.errors import AppError, ErrorCode
from app.models import Document, Evidence, Fact, ReviewCase
from app.models.enums import ProcessingStatus, ReviewStatus
from app.services.conflicts import detect_conflicts
from app.services.extraction import extract_facts
from app.services.ocr import OcrEngine
from app.services.processing import mark_failed, process_document
from app.storage.base import StorageBackend

logger = logging.getLogger("carelynx.pipeline")

PROCESSABLE = (ProcessingStatus.UPLOADED, ProcessingStatus.FAILED)


def purge_document_facts(db: Session, doc: Document) -> None:
    """Delete facts evidenced by this document (+ their open reviews) so re-processing cannot duplicate."""
    fact_ids = set(db.scalars(select(Evidence.fact_id).where(Evidence.document_id == doc.id)).all())
    if not fact_ids:
        return
    str_ids = {str(i) for i in fact_ids}
    open_reviews = db.scalars(
        select(ReviewCase).where(ReviewCase.case_id == doc.case_id, ReviewCase.status == ReviewStatus.OPEN)
    ).all()
    for review in open_reviews:
        if str_ids & {str(x) for x in review.fact_ids or []}:
            db.delete(review)
    for fact in db.scalars(select(Fact).where(Fact.id.in_(fact_ids))).all():
        db.delete(fact)
    db.flush()


def _claim(db: Session, doc: Document) -> ProcessingStatus:
    """Atomically move UPLOADED/FAILED → PROCESSING; concurrent or repeated calls get 409."""
    previous = doc.processing_status
    claimed = db.execute(
        update(Document)
        .where(Document.id == doc.id, Document.processing_status.in_(PROCESSABLE))
        .values(processing_status=ProcessingStatus.PROCESSING)
    ).rowcount  # type: ignore[attr-defined]  # CursorResult for UPDATE
    if claimed != 1:
        db.rollback()
        raise AppError(
            ErrorCode.INVALID_STATE, "Document was already processed or is being processed.", 409
        )
    return previous


async def run_document(db: Session, storage: StorageBackend, doc: Document, *, ocr: OcrEngine) -> Document:
    if _claim(db, doc) == ProcessingStatus.FAILED:
        purge_document_facts(db, doc)
    db.commit()

    doc = process_document(db, storage, doc, ocr)
    if doc.processing_status == ProcessingStatus.FAILED:
        return doc

    doc_id: uuid.UUID = doc.id
    try:
        await extract_facts(db, doc)
        detect_conflicts(db, doc.case_id)
        db.commit()
    except Exception as exc:  # noqa: BLE001 — a partial extraction must never be left looking processed
        db.rollback()
        provider_failed = isinstance(exc, ProviderError)
        logger.warning("Extraction failed document_id=%s err=%s", doc_id, type(exc).__name__)
        if not provider_failed:
            logger.exception("Unexpected extraction failure document_id=%s", doc_id)
        doc = db.get_one(Document, doc_id)
        purge_document_facts(db, doc)
        mark_failed(db, doc, ErrorCode.MODEL_ERROR if provider_failed else ErrorCode.INTERNAL_ERROR)
        db.commit()
        if provider_failed:
            raise AppError(
                ErrorCode.MODEL_ERROR,
                "Inference failed; no information was extracted. The document was sent for human review.",
                502,
            ) from exc
    return doc
