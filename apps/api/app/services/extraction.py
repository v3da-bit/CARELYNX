import logging

from sqlalchemy.orm import Session

from app.ai.factory import get_inference_provider
from app.ai.prompts import render_extraction_prompt
from app.ai.provider import PageInput, ProviderError, StructuredRequest
from app.ai.schemas import ExtractionOutput
from app.models import Document, Evidence, Fact
from app.models.entities import ReviewCase
from app.models.enums import ActorType, AuditEvent, FactStatus, FactType, ReviewReason, ReviewSeverity, ReviewStatus
from app.safety.evidence import match_verbatim_across_pages
from app.safety.policy import check_safety_policy
from app.safety.status import compute_fact_status
from app.services import audit

logger = logging.getLogger(__name__)


def _open_review(
    db: Session,
    *,
    case_id,
    document_id,
    fact_id,
    reason: str,
    reason_code: ReviewReason,
    severity: ReviewSeverity,
) -> None:
    review = ReviewCase(
        case_id=case_id,
        reason=reason,
        reason_code=reason_code,
        severity=severity,
        document_id=document_id,
        fact_ids=[str(fact_id)],
        status=ReviewStatus.OPEN,
    )
    db.add(review)
    audit.record(
        db,
        AuditEvent.REVIEW_CREATED,
        actor_type=ActorType.SYSTEM,
        case_id=case_id,
        document_id=document_id,
        review_reason=reason_code.value,
    )


async def extract_facts(db: Session, doc: Document) -> None:
    """Extract facts from a processed document using the InferenceProvider."""
    if doc.page_count == 0 or not doc.pages:
        logger.info("Document %s has no pages, skipping extraction.", doc.id)
        return

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
        context={"pages": [{"page_number": p.page_number, "text": p.text} for p in doc.pages]},
    )

    try:
        raw_output = await provider.generate_structured(request)
        output = ExtractionOutput.model_validate(raw_output)
    except Exception as exc:
        logger.error("Extraction failed for document_id=%s: %s", doc.id, exc)
        raise ProviderError(f"Inference provider failed without fabricating facts: {exc}") from exc

    for candidate in output.facts:
        match = match_verbatim_across_pages(
            page_texts, candidate.source.quote, candidate.source.page_number
        )
        page = pages_by_number.get(match.page_number or candidate.source.page_number)

        is_safe, violations = check_safety_policy(candidate.value.model_dump())
        decision = compute_fact_status(
            evidence_verified=match.verified,
            page_quality=page.text_quality if page is not None else None,
            ocr_confidence=page.ocr_confidence if page is not None else None,
            extraction_method=page.extraction_method if page is not None else None,
            provider_legible=candidate.legible,
            safety_ok=is_safe,
            safety_violations=violations,
        )

        fact = Fact(
            case_id=doc.case_id,
            fact_type=FactType(candidate.fact_type),
            value=candidate.value.model_dump(),
            status=decision.status,
            confidence=decision.confidence,
            status_reasons=list(decision.reasons),
            extracted_by=provider.info.name,
        )
        db.add(fact)
        db.flush()

        evidence = Evidence(
            fact_id=fact.id,
            document_id=doc.id,
            page_number=match.page_number or candidate.source.page_number,
            section=candidate.source.section,
            snippet=candidate.source.quote,
            char_start=match.char_start,
            char_end=match.char_end,
            verified=match.verified,
        )
        db.add(evidence)
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
            _open_review(
                db,
                case_id=doc.case_id,
                document_id=doc.id,
                fact_id=fact.id,
                reason="; ".join(decision.reasons) or "Safety policy block",
                reason_code=decision.review_reason or ReviewReason.SAFETY_BLOCK,
                severity=ReviewSeverity.HIGH,
            )
        elif decision.review_reason is not None:
            _open_review(
                db,
                case_id=doc.case_id,
                document_id=doc.id,
                fact_id=fact.id,
                reason="; ".join(decision.reasons) or "Human review required",
                reason_code=decision.review_reason,
                severity=ReviewSeverity.MEDIUM,
            )

    audit.record(
        db,
        AuditEvent.AI_EXTRACTION,
        actor_type=ActorType.SYSTEM,
        case_id=doc.case_id,
        document_id=doc.id,
        extracted_facts_count=len(output.facts),
        provider_name=provider.info.name,
    )

    db.commit()
