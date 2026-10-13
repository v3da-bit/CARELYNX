"""Deterministic fact-status calculator (FR-009, AI_INSTRUCTIONS §5.3).

The model never declares its own certainty. Status and confidence are computed here from signals the
application measured itself (CLAUDE.md §10):

  confidence = min(page text quality, OCR confidence if any, quality of the quoted line)
               × 0 if evidence unverified / text illegible, capped at 0.5 if a key field could not be parsed

Hard gates come first (safety → evidence → OCR availability → legibility → OCR-read page → page quality →
OCR confidence); then the confidence floor SAFETY_MIN_FACT_CONFIDENCE is applied. Confidence is a
decision-support signal, not a guarantee. Conflict status is applied later by `app.services.conflicts`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from app.core.config import get_settings
from app.models.enums import ExtractionMethod, FactStatus, ReviewReason

# Fields without which a fact of this type is not actionable (domain validation signal).
KEY_FIELDS: dict[str, tuple[str, ...]] = {
    "follow_up": ("date",),
    "medication": ("strength",),
    "encounter_date": ("date",),
}
MISSING_FIELD_CAP = 0.5


@dataclass(frozen=True)
class StatusDecision:
    status: FactStatus
    reasons: list[str] = field(default_factory=list)
    confidence: float = 0.0
    review_reason: ReviewReason | None = None


def missing_key_fields(fact_type: str, value: dict[str, Any]) -> list[str]:
    return [f for f in KEY_FIELDS.get(fact_type, ()) if not value.get(f)]


def compute_fact_status(
    *,
    evidence_verified: bool,
    page_quality: float | None,
    ocr_confidence: float | None,
    extraction_method: ExtractionMethod | None,
    provider_legible: bool,
    safety_ok: bool,
    safety_violations: list[str] | None = None,
    quote_quality: float | None = None,
    missing_fields: Sequence[str] = (),
    min_page_quality: float | None = None,
    min_fact_confidence: float | None = None,
) -> StatusDecision:
    settings = get_settings()
    quality_floor = settings.safety_min_page_quality if min_page_quality is None else min_page_quality
    confidence_floor = (
        settings.safety_min_fact_confidence if min_fact_confidence is None else min_fact_confidence
    )

    if not safety_ok:
        reasons = list(safety_violations or ["Safety policy rejected an unsupported clinical claim"])
        return StatusDecision(FactStatus.REJECTED, reasons, 0.0, ReviewReason.SAFETY_BLOCK)

    if not evidence_verified:
        return StatusDecision(
            FactStatus.HUMAN_REQUIRED,
            ["Missing verbatim evidence on the cited source page"],
            0.0,
            ReviewReason.MISSING_EVIDENCE,
        )

    if extraction_method == ExtractionMethod.OCR_UNAVAILABLE:
        return StatusDecision(
            FactStatus.HUMAN_REQUIRED,
            ["OCR unavailable; scanned page text cannot be verified"],
            0.0,
            ReviewReason.OCR_UNAVAILABLE,
        )

    if not provider_legible:
        return StatusDecision(
            FactStatus.HUMAN_REQUIRED,
            ["Source text could not be read reliably; CARELYNX will not guess"],
            0.0,
            ReviewReason.LOW_TEXT_QUALITY,
        )

    signals = [0.0 if page_quality is None else float(page_quality)]
    if ocr_confidence is not None:
        signals.append(float(ocr_confidence))
    if quote_quality is not None:
        signals.append(float(quote_quality))
    confidence = round(min(signals), 4)
    if missing_fields:
        confidence = min(confidence, MISSING_FIELD_CAP)

    if extraction_method == ExtractionMethod.OCR:
        return StatusDecision(
            FactStatus.NEEDS_REVIEW,
            ["Text was read by OCR from a scanned image; a human must confirm it"],
            confidence,
            ReviewReason.LOW_CONFIDENCE,
        )

    quality = signals[0]
    if quality < quality_floor:
        return StatusDecision(
            FactStatus.NEEDS_REVIEW,
            [f"Page text quality {quality:.2f} is below threshold {quality_floor:.2f}"],
            confidence,
            ReviewReason.LOW_TEXT_QUALITY,
        )

    if ocr_confidence is not None and float(ocr_confidence) < quality_floor:
        return StatusDecision(
            FactStatus.NEEDS_REVIEW,
            [f"OCR confidence {float(ocr_confidence):.2f} is below threshold {quality_floor:.2f}"],
            confidence,
            ReviewReason.LOW_CONFIDENCE,
        )

    if confidence < confidence_floor:
        reasons = [f"Application confidence {confidence:.2f} is below {confidence_floor:.2f}"]
        if missing_fields:
            reasons.append(f"Could not read: {', '.join(missing_fields)}")
        return StatusDecision(FactStatus.NEEDS_REVIEW, reasons, confidence, ReviewReason.LOW_CONFIDENCE)

    return StatusDecision(
        FactStatus.VERIFIED, ["Verbatim evidence confirmed by application code"], confidence
    )
