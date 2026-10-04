import logging

from sqlalchemy.orm import Session

from app.ai.factory import get_inference_provider
from app.ai.prompts import render_extraction_prompt
from app.ai.provider import PageInput, StructuredRequest
from app.ai.schemas import ExtractionOutput
from app.models import Document, Evidence, Fact
from app.models.enums import ActorType, AuditEvent, FactStatus, FactType
from app.services import audit

logger = logging.getLogger(__name__)

async def extract_facts(db: Session, doc: Document) -> None:
    """Extract facts from a processed document using the InferenceProvider."""
    if doc.page_count == 0 or not doc.pages:
        logger.info(f"Document {doc.id} has no pages, skipping extraction.")
        return

    provider = get_inference_provider()
    
    pages_input = [
        PageInput(page_number=p.page_number, text=p.text or "")
        for p in doc.pages
    ]

    schema = ExtractionOutput.model_json_schema()
    system_prompt, user_prompt = render_extraction_prompt(pages_input, schema)
    
    request = StructuredRequest(
        task="extraction_v1",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        json_schema=schema,
        context={"pages": [{"page_number": p.page_number, "text": p.text} for p in doc.pages]}
    )

    try:
        raw_output = await provider.generate_structured(request)
        # Validate raw output against Pydantic model
        output = ExtractionOutput.model_validate(raw_output)
    except Exception as e:
        logger.error(f"Extraction failed for document_id={doc.id}: {e}")
        # Could log this to audit and fail, but for now just log it
        raise e

    for candidate in output.facts:
        # Verify evidence
        verified = False
        page_text = None
        for p in doc.pages:
            if p.page_number == candidate.source.page_number:
                page_text = p.text
                break
        
        char_start, char_end = None, None
        if page_text and candidate.source.quote in page_text:
            verified = True
            char_start = page_text.find(candidate.source.quote)
            char_end = char_start + len(candidate.source.quote)

        # Determine initial fact status
        initial_status = FactStatus.VERIFIED if candidate.legible and verified else FactStatus.HUMAN_REQUIRED

        fact = Fact(
            case_id=doc.case_id,
            fact_type=FactType(candidate.fact_type),
            value=candidate.value.model_dump(),
            status=initial_status,
            confidence=1.0 if (candidate.legible and verified) else 0.0,
            extracted_by=provider.info.name
        )
        db.add(fact)
        db.flush() # flush to get fact.id

        evidence = Evidence(
            fact_id=fact.id,
            document_id=doc.id,
            page_number=candidate.source.page_number,
            section=candidate.source.section,
            snippet=candidate.source.quote,
            char_start=char_start,
            char_end=char_end,
            verified=verified
        )
        db.add(evidence)
    
    audit.record(
        db,
        AuditEvent.AI_EXTRACTION,
        actor_type=ActorType.SYSTEM,
        case_id=doc.case_id,
        document_id=doc.id,
        extracted_facts_count=len(output.facts),
        provider_name=provider.info.name
    )
    
    db.commit()
