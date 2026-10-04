import logging
from sqlalchemy.orm import Session
from app.ai.factory import get_inference_provider
from app.ai.provider import StructuredRequest
from app.models.entities import Fact
from sqlalchemy import select

logger = logging.getLogger(__name__)

async def translate_facts(db: Session, case_id: str, target_lang: str) -> dict:
    """Translate facts using the InferenceProvider."""
    facts = db.scalars(select(Fact).where(Fact.case_id == case_id)).all()
    
    if not facts:
        return {"translated_facts": []}

    provider = get_inference_provider()
    
    # We construct a prompt to translate the fact values safely.
    # Medical translation must retain uncertainty and not alter meaning.
    system_prompt = f"""You are a professional medical translator. 
Translate the provided medical facts into {target_lang}. 
CRITICAL RULES:
- Maintain all uncertainty. If something says "possible", translate it as "possible".
- Do not add any new information.
- Output ONLY the translated values in a JSON array matching the input structure."""

    facts_json = [{"id": str(f.id), "type": f.fact_type, "value": f.value, "status": f.status} for f in facts]
    
    user_prompt = f"Translate these facts to {target_lang}:\n" + str(facts_json)
    
    schema = {
        "type": "object",
        "properties": {
            "translated_facts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "translated_value": {"type": "object"}
                    }
                }
            }
        },
        "required": ["translated_facts"]
    }

    request = StructuredRequest(
        task="translation_v1",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        json_schema=schema,
        context={"target_lang": target_lang}
    )

    try:
        raw_output = await provider.generate_structured(request)
        return raw_output
    except Exception as e:
        logger.error(f"Translation failed for case_id={case_id}: {e}")
        raise e
