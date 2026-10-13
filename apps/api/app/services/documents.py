"""Case + document intake services."""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.models import Case, Document, Patient
from app.models.enums import ActorType, AuditEvent, Language, ProcessingStatus
from app.services import audit
from app.services.upload_validation import check_size, sanitize_filename, sniff_file_kind
from app.storage.base import StorageBackend


def create_case(
    db: Session, preferred_language: Language = Language.EN, user_id: uuid.UUID | None = None
) -> Case:
    patient = Patient(preferred_language=preferred_language)
    db.add(patient)
    db.flush()
    case = Case(patient_id=patient.id, user_id=user_id)
    db.add(case)
    db.flush()
    audit.record(db, AuditEvent.CASE_CREATED, actor_type=ActorType.PATIENT, case_id=case.id)
    return case


def get_case(db: Session, case_id: uuid.UUID, user: Any | None = None) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise AppError(ErrorCode.NOT_FOUND, "Case not found.", 404)
    # Enforce strict user isolation: prevent Insecure Direct Object Reference (IDOR)
    if (
        user is not None
        and case.user_id is not None
        and getattr(user, "id", None) != case.user_id
        and getattr(user, "role", "patient") not in ("reviewer", "admin")
    ):
        raise AppError(ErrorCode.FORBIDDEN, "Access denied: this clinical case belongs to another account.", 403)
    return case


def list_user_cases(db: Session, user_id: uuid.UUID | None = None, limit: int = 50) -> list[Case]:
    stmt = select(Case)
    if user_id is not None:
        stmt = stmt.where(Case.user_id == user_id)
    return list(db.scalars(stmt.order_by(Case.created_at.desc()).limit(limit)).all())


def get_document(db: Session, document_id: uuid.UUID) -> Document:
    doc = db.get(Document, document_id)
    if doc is None:
        raise AppError(ErrorCode.NOT_FOUND, "Document not found.", 404)
    return doc


def upload_document(
    db: Session,
    storage: StorageBackend,
    *,
    data: bytes,
    filename: str | None,
    max_bytes: int,
    case_id: uuid.UUID | None = None,
    user: Any | None = None,
) -> Document:
    check_size(len(data), max_bytes)
    kind = sniff_file_kind(data)
    case = (
        get_case(db, case_id, user=user)
        if case_id
        else create_case(db, user_id=getattr(user, "id", None))
    )

    key = storage.put(data, kind.extension)
    try:
        doc = Document(
            case_id=case.id,
            filename=sanitize_filename(filename),
            mime_type=kind.mime_type,
            storage_key=key,
            processing_status=ProcessingStatus.UPLOADED,
            size_bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
        )
        db.add(doc)
        db.flush()
        audit.record(
            db,
            AuditEvent.DOCUMENT_UPLOADED,
            actor_type=ActorType.PATIENT,
            case_id=case.id,
            document_id=doc.id,
            mime_type=kind.mime_type,
            size_bytes=len(data),
        )
        db.commit()
    except Exception:
        db.rollback()
        storage.delete(key)
        raise
    return doc
