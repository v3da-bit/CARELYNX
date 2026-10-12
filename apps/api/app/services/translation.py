import logging
import uuid
import asyncio
from deep_translator import MyMemoryTranslator
from sqlalchemy.orm import Session
from app.ai.factory import get_inference_provider
from app.ai.provider import StructuredRequest
from app.models.entities import Fact
from sqlalchemy import select

logger = logging.getLogger(__name__)

async def translate_facts(db: Session, case_id: str, target_lang: str) -> dict:
    """Translate facts using the InferenceProvider."""
    # Ensure case_id is a UUID object for SQLAlchemy comparison
    case_uuid = uuid.UUID(case_id) if isinstance(case_id, str) else case_id
    facts = db.scalars(select(Fact).where(Fact.case_id == case_uuid)).all()
    
    if not facts:
        return {
            "case_id": case_id,
            "language": target_lang,
            "facts": []
        }

    provider = get_inference_provider()
    
    # We construct a prompt to translate the fact values safely.
    # Medical translation must retain uncertainty and not alter meaning.
    system_prompt = f"""You are a professional medical translator. 
Translate the provided medical facts into {target_lang}. 
CRITICAL RULES:
- Maintain all uncertainty. If something says "possible", translate it as "possible".
- Do not add any new information.
- Output ONLY the translated values in a JSON array matching the input structure."""

    import json
    facts_json = [{"id": str(f.id), "type": f.fact_type.value if hasattr(f.fact_type, "value") else str(f.fact_type), "value": f.value, "status": f.status.value if hasattr(f.status, "value") else str(f.status)} for f in facts]
    
    user_prompt = f"Translate these facts to {target_lang}:\n" + json.dumps(facts_json)

    
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
        
        # Handle LLM response
        translated_items = raw_output.get("translated_facts", [])
        
        # Fallback for rule_based provider which doesn't do translation natively
        if provider.info.name == "rule_based" and not translated_items:
            # Map standard lang codes to MyMemory ISO formats
            lang_map = {
                "hi": "hi-IN",
                "gu": "gu-IN",
                "en": "en-GB",
                "mr": "mr-IN",
                "ta": "ta-IN",
                "te": "te-IN"
            }
            mapped_target = lang_map.get(target_lang, target_lang)
            
            # We use deep_translator (MyMemory API, no rate limits on this IP) to do real live translations
            translator = MyMemoryTranslator(source='en-GB', target=mapped_target)
            
            async def _translate(text: str) -> str:
                # Wrap the synchronous deep_translator call in asyncio.to_thread
                # to prevent blocking the FastAPI event loop
                try:
                    res = await asyncio.to_thread(translator.translate, text)
                    return res if res else f"[{target_lang}] {text}"
                except Exception as e:
                    logger.error(f"MyMemoryTranslator failed for text '{text}': {e}")
                    # Fallback to the original text if translation API fails
                    return f"[{target_lang}] {text}"
            
            for f in facts:
                trans_val = {}
                for k, v in f.value.items():
                    if isinstance(v, str) and k in {"name", "text", "raw_text", "instruction", "substance", "kind"}:
                        trans_val[k] = await _translate(v)
                    else:
                        trans_val[k] = v
                
                translated_items.append({
                    "id": str(f.id),
                    "translated_value": trans_val
                })
        
        # Merge with original facts to match API_CONTRACTS.md
        final_facts = []
        fact_dict = {str(f.id): f for f in facts}
        for item in translated_items:
            fid = item.get("id")
            original_fact = fact_dict.get(fid)
            if original_fact:
                final_facts.append({
                    "id": fid,
                    "fact_type": original_fact.fact_type,
                    "translated_value": item.get("translated_value", {}),
                    "status": original_fact.status
                })
                
        return {
            "case_id": case_id,
            "language": target_lang,
            "facts": final_facts
        }
    except Exception as e:
        logger.error(f"Translation failed for case_id={case_id}: {e}")
        raise e
