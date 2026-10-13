"""Structured fact extraction: provider → Pydantic validation → evidence check → safety policy → status →
persist.

Provider output is never trusted: every quote is re-verified against the page text, safety policy runs in
code,
and status/confidence are computed by app.safety.status. Provenance (`extracted_by`) is truthful, including
when
the configured LLM failed and the rule-based extractor was used instead.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.ai.factory import get_inference_provider
from app.ai.prompts import render_extraction_prompt
from app.ai.provider import InferenceProvider, PageInput, ProviderError, StructuredRequest
from app.ai.rule_based import RuleBasedProvider
from app.ai.schemas import ExtractionOutput
from app.models import Document, Evidence, Fact
from app.models.entities import ReviewCase
from app.models.enums import (
    ActorType,
    AuditEvent,
    ExtractionMethod,
    FactStatus,
    FactType,
    ReviewReason,
    ReviewSeverity,
    ReviewStatus,
)
from app.safety.evidence import match_verbatim_across_pages
from app.safety.policy import check_safety_policy
from app.safety.status import compute_fact_status, missing_key_fields
from app.safety.text_quality import line_quality
from app.services import audit

logger = logging.getLogger(__name__)

# SAFETY.md §6: any non-VERIFIED status on these opens a HIGH-severity review.
HIGH_RISK_TYPES = frozenset(
    {FactType.ALLERGY, FactType.MEDICATION, FactType.FOLLOW_UP, FactType.WARNING_SIGN}
)


def review_severity(fact_type: FactType, status: FactStatus) -> ReviewSeverity:
    if fact_type in HIGH_RISK_TYPES or status == FactStatus.REJECTED:
        return ReviewSeverity.HIGH
    return ReviewSeverity.MEDIUM if status == FactStatus.HUMAN_REQUIRED else ReviewSeverity.LOW


async def run_extraction(
    provider: InferenceProvider, request: StructuredRequest
) -> tuple[ExtractionOutput, str, str | None]:
    """Return (validated output, extracted_by, fallback_reason).

    If a non-rule-based provider fails (network, malformed JSON, schema violation) we fall back to the
    rule-based extractor for demo resilience and say so in `extracted_by`. If that also fails → ProviderError
    (mapped to MODEL_ERROR by the pipeline). Nothing is ever fabricated.
    """
    try:
        raw = await provider.generate_structured(request)
        return ExtractionOutput.model_validate(raw), provider.info.name, None
    except Exception as exc:  # noqa: BLE001 — any provider/validation failure is handled below
        reason = type(exc).__name__
        if provider.info.name == "rule_based":
            raise ProviderError(f"Extraction failed ({reason}); no facts were fabricated") from exc
        logger.warning("Provider %s failed (%s); falling back to rule_based", provider.info.name, reason)
    try:
        raw = await RuleBasedProvider().generate_structured(request)
        output = ExtractionOutput.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        raise ProviderError(f"Extraction and rule-based fallback both failed ({type(exc).__name__})") from exc
    return output, f"rule_based (fallback from {provider.info.name})", reason


def _open_review(
    db: Session,
    *,
    case_id: uuid.UUID,
    document_id: uuid.UUID,
    fact_id: uuid.UUID | None,
    reason: str,
    reason_code: ReviewReason,
    severity: ReviewSeverity,
    recommended_action: str = "Check this item against the source document, then approve, correct or reject.",
) -> None:
    db.add(
        ReviewCase(
            case_id=case_id,
            reason=reason,
            reason_code=reason_code,
            severity=severity,
            document_id=document_id,
            fact_ids=[str(fact_id)] if fact_id else [],
            status=ReviewStatus.OPEN,
            recommended_action=recommended_action,
        )
    )
    audit.record(
        db,
        AuditEvent.REVIEW_CREATED,
        actor_type=ActorType.SYSTEM,
        case_id=case_id,
        document_id=document_id,
        review_reason=reason_code.value,
        severity=severity.value,
    )


async def extract_facts(db: Session, doc: Document) -> None:
    """Extract facts from a processed document using the configured InferenceProvider."""
    if doc.page_count == 0 or not doc.pages:
        logger.info("Document %s has no pages, skipping extraction.", doc.id)
        return

    unread = [p.page_number for p in doc.pages if p.extraction_method == ExtractionMethod.OCR_UNAVAILABLE]
    if unread:  # scanned pages we could not read: their content must reach a human, not vanish
        _open_review(
            db,
            case_id=doc.case_id,
            document_id=doc.id,
            fact_id=None,
            reason=f"Page(s) {', '.join(map(str, unread))} are scanned images and no OCR engine is "
            "available; "
            "their content was not read.",
            reason_code=ReviewReason.OCR_UNAVAILABLE,
            severity=ReviewSeverity.MEDIUM,
            recommended_action="Read the original scan and enter or confirm its information manually.",
        )

    provider = get_inference_provider()
    pages_input = [PageInput(page_number=p.page_number, text=p.text or "") for p in doc.pages]
    pages_by_number = {p.page_number: p for p in doc.pages}
    page_texts = {num: p.text for num, p in pages_by_number.items()}

    schema = ExtractionOutput.model_json_schema()
    system_prompt, user_prompt = render_extraction_prompt(pages_input, schema)
    request = StructuredRequest(
        task="extraction_v1",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        json_schema=schema,
        context={"pages": [{"page_number": p.page_number, "text": p.text} for p in pages_input]},
    )
    output, extracted_by, fallback_reason = await run_extraction(provider, request)

    for candidate in output.facts:
        fact_type = FactType(candidate.fact_type)
        value = candidate.value.model_dump()
        match = match_verbatim_across_pages(page_texts, candidate.source.quote, candidate.source.page_number)
        page_number = match.page_number or candidate.source.page_number
        page = pages_by_number.get(page_number)

        # A risky phrase is "documented" (allowed) only if it is inside a quote we verified on the page.
        is_safe, violations = check_safety_policy(
            value, source_quote=candidate.source.quote if match.verified else None
        )
        decision = compute_fact_status(
            evidence_verified=match.verified,
            page_quality=page.text_quality if page is not None else None,
            ocr_confidence=page.ocr_confidence if page is not None else None,
            extraction_method=page.extraction_method if page is not None else None,
            provider_legible=candidate.legible,
            safety_ok=is_safe,
            safety_violations=violations,
            quote_quality=line_quality(candidate.source.quote).score,
            missing_fields=missing_key_fields(fact_type.value, value),
        )

        fact = Fact(
            case_id=doc.case_id,
            fact_type=fact_type,
            value=value,
            status=decision.status,
            confidence=decision.confidence,
            status_reasons=list(decision.reasons),
            extracted_by=extracted_by,
        )
        db.add(fact)
        db.flush()
        db.add(
            Evidence(
                fact_id=fact.id,
                document_id=doc.id,
                page_number=page_number,
                section=candidate.source.section,
                snippet=candidate.source.quote,
                char_start=match.char_start,
                char_end=match.char_end,
                verified=match.verified,
            )
        )
        db.flush()

        if decision.status == FactStatus.REJECTED:
            audit.record(
                db,
                AuditEvent.SAFETY_BLOCK,
                actor_type=ActorType.SYSTEM,
                case_id=doc.case_id,
                document_id=doc.id,
                fact_id=str(fact.id),
            )
        if decision.review_reason is not None:
            _open_review(
                db,
                case_id=doc.case_id,
                document_id=doc.id,
                fact_id=fact.id,
                reason="; ".join(decision.reasons) or "Human review required",
                reason_code=decision.review_reason,
                severity=review_severity(fact_type, decision.status),
            )

    audit.record(
        db,
        AuditEvent.AI_EXTRACTION,
        actor_type=ActorType.SYSTEM,
        case_id=doc.case_id,
        document_id=doc.id,
        extracted_facts_count=len(output.facts),
        provider_name=extracted_by,
        model=provider.info.model if fallback_reason is None else "rule-based",
        hardware_label=provider.info.hardware_label if fallback_reason is None else "cpu (in-process)",
        fallback_from=provider.info.name if fallback_reason else None,
        fallback_reason=fallback_reason,  # exception class name only; never patient text
    )
    db.commit()
