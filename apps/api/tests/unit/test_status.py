"""Deterministic fact-status calculator tests (FR-009). The model never sets status."""

from app.models.enums import ExtractionMethod, FactStatus, ReviewReason
from app.safety.status import compute_fact_status


def _decision(**overrides):
    payload = {
        "evidence_verified": True,
        "page_quality": 0.95,
        "ocr_confidence": None,
        "extraction_method": ExtractionMethod.PDF_TEXT,
        "provider_legible": True,
        "safety_ok": True,
        "safety_violations": [],
        "min_page_quality": 0.85,
        "min_fact_confidence": 0.80,
    }
    payload.update(overrides)
    return compute_fact_status(**payload)


def test_verified_when_evidence_and_quality_pass() -> None:
    decision = _decision()
    assert decision.status == FactStatus.VERIFIED
    assert decision.review_reason is None
    assert decision.confidence == 0.95  # min of measured signals, not a hardcoded 1.0


def test_missing_evidence_is_human_required() -> None:
    decision = _decision(evidence_verified=False)
    assert decision.status == FactStatus.HUMAN_REQUIRED
    assert decision.review_reason == ReviewReason.MISSING_EVIDENCE


def test_safety_violation_is_rejected() -> None:
    decision = _decision(safety_ok=False, safety_violations=["unapproved dose change"])
    assert decision.status == FactStatus.REJECTED
    assert decision.review_reason == ReviewReason.SAFETY_BLOCK
    assert "unapproved dose change" in decision.reasons


def test_low_page_quality_needs_review() -> None:
    decision = _decision(page_quality=0.40)
    assert decision.status == FactStatus.NEEDS_REVIEW
    assert decision.review_reason == ReviewReason.LOW_TEXT_QUALITY


def test_confidence_is_min_of_signals_and_floor_applies() -> None:
    d = _decision(page_quality=0.95, quote_quality=0.65)
    assert d.status == FactStatus.NEEDS_REVIEW and d.confidence == 0.65
    assert d.review_reason == ReviewReason.LOW_CONFIDENCE
    assert (
        _decision(page_quality=0.95, quote_quality=0.65, min_fact_confidence=0.6).status
        == FactStatus.VERIFIED
    )


def test_unparsed_key_field_caps_confidence() -> None:
    d = _decision(missing_fields=["date"])
    assert d.status == FactStatus.NEEDS_REVIEW and d.confidence == 0.5
    assert any("date" in r for r in d.reasons)


def test_ocr_read_page_never_verified_even_with_high_confidence() -> None:
    d = _decision(extraction_method=ExtractionMethod.OCR, ocr_confidence=0.99)
    assert d.status == FactStatus.NEEDS_REVIEW


def test_low_ocr_confidence_needs_review() -> None:
    decision = _decision(extraction_method=ExtractionMethod.OCR, ocr_confidence=0.50)
    assert decision.status == FactStatus.NEEDS_REVIEW
    assert decision.review_reason == ReviewReason.LOW_CONFIDENCE


def test_ocr_unavailable_is_human_required() -> None:
    decision = _decision(extraction_method=ExtractionMethod.OCR_UNAVAILABLE)
    assert decision.status == FactStatus.HUMAN_REQUIRED
    assert decision.review_reason == ReviewReason.OCR_UNAVAILABLE


def test_illegible_provider_flag_is_human_required() -> None:
    decision = _decision(provider_legible=False)
    assert decision.status == FactStatus.HUMAN_REQUIRED
    assert decision.review_reason == ReviewReason.LOW_TEXT_QUALITY
