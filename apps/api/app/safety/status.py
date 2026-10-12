"""Deterministic fact-status calculator (FR-009, AI_INSTRUCTIONS §5.3).

The model must never declare its own certainty. Status is computed here from
evidence, page quality, OCR availability, and safety-policy results.
Conflict status is applied later by `app.services.conflicts`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import get_settings
from app.models.enums import ExtractionMethod, FactStatus, ReviewReason


@dataclass(frozen=True)
class StatusDecision:
    status: FactStatus
    reasons: list[str] = field(default_factory=list)
    confidence: float = 0.0
    review_reason: ReviewReason | None = None


def compute_fact_status(
    *,
    evidence_verified: bool,
    page_quality: float | None,
    ocr_confidence: float | None,
    extraction_method: ExtractionMethod | None,
    provider_legible: bool,
    safety_ok: bool,
    safety_violations: list[str] | None = None,
    min_page_quality: float | None = None,
    min_fact_confidence: float | None = None,
) -> StatusDecision:
    settings = get_settings()
    quality_floor = settings.safety_min_page_quality if min_page_quality is None else min_page_quality
    confidence_floor = settings.safety_min_fact_confidence if min_fact_confidence is None else min_fact_confidence

    reasons: list[str] = []
    violations = safety_violations or []

    if not safety_ok:
        reasons.extend(violations or ["Safety policy rejected an unsupported clinical claim"])
        return StatusDecision(FactStatus.REJECTED, reasons, 0.0, ReviewReason.SAFETY_BLOCK)

    if not evidence_verified:
        reasons.append("Missing verbatim evidence on the cited source page")
        return StatusDecision(FactStatus.HUMAN_REQUIRED, reasons, 0.0, ReviewReason.MISSING_EVIDENCE)

    if extraction_method == ExtractionMethod.OCR_UNAVAILABLE:
        reasons.append("OCR unavailable; scanned page text cannot be verified")
        return StatusDecision(FactStatus.HUMAN_REQUIRED, reasons, 0.0, ReviewReason.OCR_UNAVAILABLE)

    if not provider_legible:
        reasons.append("Source text was marked illegible; do not present as verified")
        return StatusDecision(FactStatus.HUMAN_REQUIRED, reasons, 0.0, ReviewReason.LOW_TEXT_QUALITY)

    quality = 0.0 if page_quality is None else float(page_quality)
    if quality < quality_floor:
        reasons.append(f"Page text quality {quality:.2f} is below threshold {quality_floor:.2f}")
        return StatusDecision(FactStatus.NEEDS_REVIEW, reasons, quality, ReviewReason.LOW_TEXT_QUALITY)

    if ocr_confidence is not None and float(ocr_confidence) < quality_floor:
        reasons.append(
            f"OCR confidence {float(ocr_confidence):.2f} is below threshold {quality_floor:.2f}"
        )
        return StatusDecision(FactStatus.NEEDS_REVIEW, reasons, float(ocr_confidence), ReviewReason.LOW_CONFIDENCE)

    # Evidence-backed facts start at 1.0; the confidence floor is reserved for
    # future provider-supplied scores that application code still owns.
    confidence = 1.0
    if confidence < confidence_floor:
        reasons.append(f"Application confidence {confidence:.2f} is below {confidence_floor:.2f}")
        return StatusDecision(FactStatus.NEEDS_REVIEW, reasons, confidence, ReviewReason.LOW_CONFIDENCE)

    return StatusDecision(FactStatus.VERIFIED, ["Verbatim evidence confirmed by application code"], confidence, None)
