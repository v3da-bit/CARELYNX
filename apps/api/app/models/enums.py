"""Domain enums. Single source of truth — no magic strings elsewhere."""

from __future__ import annotations

from enum import StrEnum


class CaseStatus(StrEnum):
    OPEN = "OPEN"
    PROCESSING = "PROCESSING"
    READY = "READY"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ProcessingStatus(StrEnum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    PROCESSED_WITH_WARNINGS = "PROCESSED_WITH_WARNINGS"
    FAILED = "FAILED"


class DocumentKind(StrEnum):
    DISCHARGE_SUMMARY = "discharge_summary"
    PRESCRIPTION = "prescription"
    FOLLOW_UP = "follow_up"
    UNKNOWN = "unknown"


class ExtractionMethod(StrEnum):
    PDF_TEXT = "pdf_text"
    OCR = "ocr"
    OCR_UNAVAILABLE = "ocr_unavailable"
    FAILED = "failed"


class FactStatus(StrEnum):
    VERIFIED = "VERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    REJECTED = "REJECTED"


class FactType(StrEnum):
    FOLLOW_UP = "follow_up"
    MEDICATION = "medication"
    INSTRUCTION = "instruction"
    WARNING_SIGN = "warning_sign"
    ALLERGY = "allergy"
    DOCUMENTED_CONDITION = "documented_condition"
    ENCOUNTER_DATE = "encounter_date"


class ConflictStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class ReviewStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class ReviewSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ReviewReason(StrEnum):
    CONFLICT = "CONFLICT"
    LOW_TEXT_QUALITY = "LOW_TEXT_QUALITY"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    SAFETY_BLOCK = "SAFETY_BLOCK"
    OCR_UNAVAILABLE = "OCR_UNAVAILABLE"
    PROCESSING_FAILED = "PROCESSING_FAILED"


class ReviewDecision(StrEnum):
    """Explicitly modelled reviewer decisions (API_CONTRACTS.md: no arbitrary strings)."""

    APPROVE = "APPROVE"  # approve the flagged fact(s) exactly as extracted from source
    REJECT = "REJECT"  # reject the flagged fact(s); they will not be shown as information
    SELECT_SOURCE = "SELECT_SOURCE"  # conflicts: approve one fact (by id), reject the others
    CORRECT_VALUE = "CORRECT_VALUE"  # reviewer enters the verified value after checking the source


class ActorType(StrEnum):
    SYSTEM = "SYSTEM"
    AI = "AI"
    PATIENT = "PATIENT"
    REVIEWER = "REVIEWER"


class AuditEvent(StrEnum):
    CASE_CREATED = "CASE_CREATED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_PROCESSING_STARTED = "DOCUMENT_PROCESSING_STARTED"
    DOCUMENT_PROCESSED = "DOCUMENT_PROCESSED"
    DOCUMENT_PROCESSING_FAILED = "DOCUMENT_PROCESSING_FAILED"
    AI_EXTRACTION = "AI_EXTRACTION"
    SAFETY_BLOCK = "SAFETY_BLOCK"
    CONFLICT_CREATED = "CONFLICT_CREATED"
    REVIEW_CREATED = "REVIEW_CREATED"
    REVIEW_RESOLVED = "REVIEW_RESOLVED"
    CARE_PLAN_GENERATED = "CARE_PLAN_GENERATED"
    TRANSLATION_GENERATED = "TRANSLATION_GENERATED"
    DOCUMENT_ACCESSED = "DOCUMENT_ACCESSED"


class Language(StrEnum):
    EN = "en"
    HI = "hi"
    GU = "gu"
