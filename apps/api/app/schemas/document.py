"""Document / case API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import CaseStatus, DocumentKind, ExtractionMethod, ProcessingStatus


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(ORM):
    id: uuid.UUID
    case_id: uuid.UUID
    filename: str
    status: ProcessingStatus


class PageSummary(ORM):
    page_number: int
    extraction_method: ExtractionMethod
    text_quality: float | None
    ocr_confidence: float | None
    quality_flags: list[str]


class PageDetail(PageSummary):
    document_id: uuid.UUID
    text: str | None


class DocumentOut(ORM):
    id: uuid.UUID
    case_id: uuid.UUID
    filename: str
    mime_type: str
    size_bytes: int
    page_count: int | None
    processing_status: ProcessingStatus
    document_kind: DocumentKind
    error_code: str | None
    created_at: datetime
    pages: list[PageSummary] = []


class ProcessResponse(BaseModel):
    document_id: uuid.UUID
    status: ProcessingStatus


class CaseCreated(ORM):
    id: uuid.UUID
    status: CaseStatus


class CaseCounts(BaseModel):
    verified: int = 0
    needs_review: int = 0
    human_required: int = 0
    conflict_detected: int = 0
    rejected: int = 0
    open_reviews: int = 0


class CaseOut(ORM):
    id: uuid.UUID
    status: CaseStatus
    created_at: datetime
    documents: list[DocumentOut]
    counts: CaseCounts
