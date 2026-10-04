"""ORM models for every table in docs/DATABASE.md (+ documented additive columns)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Timestamps, UUIDPk, enum_col, utcnow
from app.models.enums import (
    ActorType,
    CaseStatus,
    ConflictStatus,
    DocumentKind,
    ExtractionMethod,
    FactStatus,
    FactType,
    Language,
    ProcessingStatus,
    ReviewDecision,
    ReviewReason,
    ReviewSeverity,
    ReviewStatus,
)

CONFIDENCE = Numeric(5, 4, asdecimal=False)


class Patient(UUIDPk, Timestamps, Base):
    __tablename__ = "patients"
    preferred_language: Mapped[Language] = mapped_column(enum_col(Language), default=Language.EN)
    external_reference: Mapped[str | None] = mapped_column(Text)


class Case(UUIDPk, Timestamps, Base):
    __tablename__ = "cases"
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    status: Mapped[CaseStatus] = mapped_column(enum_col(CaseStatus), default=CaseStatus.OPEN)

    documents: Mapped[list[Document]] = relationship(back_populates="case", order_by="Document.created_at")


class Document(UUIDPk, Timestamps, Base):
    __tablename__ = "documents"
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(Text)
    mime_type: Mapped[str] = mapped_column(String(100))
    storage_key: Mapped[str] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        enum_col(ProcessingStatus), default=ProcessingStatus.UPLOADED
    )
    # additive columns
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(64), default="")
    document_kind: Mapped[DocumentKind] = mapped_column(enum_col(DocumentKind), default=DocumentKind.UNKNOWN)
    error_code: Mapped[str | None] = mapped_column(String(64))

    case: Mapped[Case] = relationship(back_populates="documents")
    pages: Mapped[list[DocumentPage]] = relationship(
        back_populates="document", order_by="DocumentPage.page_number", cascade="all, delete-orphan"
    )


class DocumentPage(UUIDPk, Base):
    __tablename__ = "document_pages"
    __table_args__ = (UniqueConstraint("document_id", "page_number", name="uq_document_pages_doc_page"),)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str | None] = mapped_column(Text)
    ocr_confidence: Mapped[float | None] = mapped_column(CONFIDENCE)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    # additive columns
    extraction_method: Mapped[ExtractionMethod] = mapped_column(enum_col(ExtractionMethod))
    text_quality: Mapped[float | None] = mapped_column(CONFIDENCE)
    quality_flags: Mapped[list[Any]] = mapped_column(default=list)

    document: Mapped[Document] = relationship(back_populates="pages")


class Fact(UUIDPk, Timestamps, Base):
    __tablename__ = "facts"
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    fact_type: Mapped[FactType] = mapped_column(enum_col(FactType))
    value: Mapped[dict[str, Any]] = mapped_column()
    status: Mapped[FactStatus] = mapped_column(enum_col(FactStatus))
    confidence: Mapped[float | None] = mapped_column(CONFIDENCE)
    # additive columns
    status_reasons: Mapped[list[Any]] = mapped_column(default=list)
    extracted_by: Mapped[str] = mapped_column(String(100), default="")
    human_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    evidence: Mapped[list[Evidence]] = relationship(back_populates="fact", cascade="all, delete-orphan")


class Evidence(UUIDPk, Base):
    __tablename__ = "evidence"
    fact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("facts.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    section: Mapped[str | None] = mapped_column(Text)
    snippet: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    # additive columns
    char_start: Mapped[int | None] = mapped_column(Integer)
    char_end: Mapped[int | None] = mapped_column(Integer)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

    fact: Mapped[Fact] = relationship(back_populates="evidence")


class Conflict(UUIDPk, Base):
    __tablename__ = "conflicts"
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    fact_type: Mapped[FactType] = mapped_column(enum_col(FactType))
    conflict_data: Mapped[dict[str, Any]] = mapped_column()
    status: Mapped[ConflictStatus] = mapped_column(enum_col(ConflictStatus), default=ConflictStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column()


class ReviewCase(UUIDPk, Base):
    __tablename__ = "review_cases"
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    reason: Mapped[str] = mapped_column(Text)
    severity: Mapped[ReviewSeverity] = mapped_column(enum_col(ReviewSeverity))
    status: Mapped[ReviewStatus] = mapped_column(enum_col(ReviewStatus), default=ReviewStatus.OPEN)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column()
    resolution: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column()
    # additive columns
    reason_code: Mapped[ReviewReason] = mapped_column(enum_col(ReviewReason))
    fact_ids: Mapped[list[Any]] = mapped_column(default=list)
    conflict_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("conflicts.id", ondelete="SET NULL"))
    document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"))
    recommended_action: Mapped[str] = mapped_column(Text, default="")
    decision: Mapped[ReviewDecision | None] = mapped_column(enum_col(ReviewDecision))
    resolved_by: Mapped[str | None] = mapped_column(String(100))


class AuditLog(UUIDPk, Base):
    __tablename__ = "audit_logs"
    case_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    actor_type: Mapped[ActorType] = mapped_column(enum_col(ActorType))
    actor_id: Mapped[uuid.UUID | None] = mapped_column()
    event_type: Mapped[str] = mapped_column(String(100))
    # 'metadata' is reserved on declarative classes → attribute name differs, column name matches spec.
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", default=dict)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
