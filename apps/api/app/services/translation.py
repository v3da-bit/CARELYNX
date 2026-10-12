import asyncio
import html
import json
import logging
import os
import uuid
from typing import Any
from deep_translator import MyMemoryTranslator
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.factory import get_inference_provider
from app.ai.provider import StructuredRequest
from app.core.config import get_settings
from app.models.entities import Fact

logger = logging.getLogger(__name__)

GOOGLE_TRANSLATE_API_URL = "https://translation.googleapis.com/language/translate/v2"

# Supported target languages per specification:
# English (en), हिन्दी (hi), ગુજરાતી (gu), मराठी (mr), தமிழ் (ta), తెలుగు (te)
SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "हिन्दी",
    "gu": "ગુજરાતી",
    "mr": "मराठी",
    "ta": "தமிழ்",
    "te": "తెలుగు",
}

# In-memory translation cache keyed by (case_id_str, target_lang)
_TRANSLATION_CACHE: dict[tuple[str, str], dict[str, Any]] = {}


def clear_translation_cache(case_id: str | None = None) -> None:
    """Clear memory cache for a given case_id or all cases."""
    global _TRANSLATION_CACHE
    if case_id is None:
        _TRANSLATION_CACHE.clear()
    else:
        _TRANSLATION_CACHE = {k: v for k, v in _TRANSLATION_CACHE.items() if k[0] != case_id}


async def translate_with_google_v2(
    texts: list[str],
    target_lang: str,
    source_lang: str = "en",
    api_key: str | None = None,
    timeout: float = 12.0,
) -> list[str]:
    """
    Translates a list of strings using Google Cloud Translation API v2:
    POST https://translation.googleapis.com/language/translate/v2
    """
    if not texts:
        return []

    if target_lang == "en" or target_lang == source_lang:
        return list(texts)

    key = api_key or get_settings().google_translate_api_key or os.environ.get("GOOGLE_TRANSLATE_API_KEY", "")
    if not key:
        raise ValueError("Google Translate API key not configured")

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": key,
    }
    # If the key is an OAuth Bearer token (starts with ya29.)
    if key.startswith("ya29."):
        headers["Authorization"] = f"Bearer {key}"
        url = GOOGLE_TRANSLATE_API_URL
    else:
        url = f"{GOOGLE_TRANSLATE_API_URL}?key={key}"

    payload = {
        "q": texts,
        "target": target_lang,
        "source": source_lang,
        "format": "text",
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    translations_data = data.get("data", {}).get("translations", [])
    results: list[str] = []
    for item in translations_data:
        raw_translated = item.get("translatedText", "")
        # Google Translate v2 returns HTML entity escapes (e.g. &#39;, &quot;) even with format="text"
        clean_text = html.unescape(raw_translated)
        results.append(clean_text)

    # Pad with originals if count differs
    if len(results) < len(texts):
        results.extend(texts[len(results):])

    return results


async def translate_facts(db: Session, case_id: str, target_lang: str) -> dict[str, Any]:
    """Translate facts using Google Cloud Translation v2 when configured, with safe inference fallback."""
    case_uuid = uuid.UUID(case_id) if isinstance(case_id, str) else case_id
    facts = db.scalars(select(Fact).where(Fact.case_id == case_uuid)).all()

    if not facts:
        return {
            "case_id": case_id,
            "language": target_lang,
            "facts": [],
        }

    # If target language is English, return directly without network overhead
    if target_lang == "en":
        return {
            "case_id": case_id,
            "language": "en",
            "facts": [
                {
                    "id": str(f.id),
                    "fact_type": f.fact_type.value if hasattr(f.fact_type, "value") else str(f.fact_type),
                    "translated_value": f.value,
                    "status": f.status.value if hasattr(f.status, "value") else str(f.status),
                }
                for f in facts
            ],
        }

    # Check cache first
    cache_key = (str(case_id), target_lang)
    if cache_key in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[cache_key]

    # Attempt Google Cloud Translation v2 first if API key is provided
    google_key = get_settings().google_translate_api_key or os.environ.get("GOOGLE_TRANSLATE_API_KEY", "")
    if google_key:
        try:
            translatable_keys = {"name", "text", "raw_text", "instruction", "substance", "kind", "notes", "department", "reaction"}
            
            # Extract list of texts to batch translate
            items_to_translate: list[tuple[str, str, str]] = []  # (fact_id, key, text)
            for f in facts:
                if isinstance(f.value, dict):
                    for k, v in f.value.items():
                        if isinstance(v, str) and k in translatable_keys and v.strip():
                            items_to_translate.append((str(f.id), k, v))

            if items_to_translate:
                texts = [item[2] for item in items_to_translate]
                translated_texts = await translate_with_google_v2(texts, target_lang, api_key=google_key)

                # Reconstruct translated dictionaries per fact
                fact_trans_map: dict[str, dict[str, Any]] = {str(f.id): dict(f.value) if isinstance(f.value, dict) else {} for f in facts}
                for (fid, k, _), trans_str in zip(items_to_translate, translated_texts):
                    fact_trans_map[fid][k] = trans_str

                final_facts = [
                    {
                        "id": str(f.id),
                        "fact_type": f.fact_type.value if hasattr(f.fact_type, "value") else str(f.fact_type),
                        "translated_value": fact_trans_map.get(str(f.id), f.value),
                        "status": f.status.value if hasattr(f.status, "value") else str(f.status),
                    }
                    for f in facts
                ]
                
                result = {
                    "case_id": case_id,
                    "language": target_lang,
                    "facts": final_facts,
                    "provider": "google_translate_v2",
                }
                _TRANSLATION_CACHE[cache_key] = result
                return result
        except Exception as e:
            logger.warning(f"Google Cloud Translation v2 failed, falling back to inference provider: {e}")

    # Fallback to InferenceProvider / Rule-Based provider
    provider = get_inference_provider()

    system_prompt = f"""You are a professional medical translator. 
Translate the provided medical facts into {target_lang}. 
CRITICAL RULES:
- Maintain all uncertainty. If something says "possible", translate it as "possible".
- Do not add any new information.
- Output ONLY the translated values in a JSON array matching the input structure."""

    facts_json = [
        {
            "id": str(f.id),
            "type": f.fact_type.value if hasattr(f.fact_type, "value") else str(f.fact_type),
            "value": f.value,
            "status": f.status.value if hasattr(f.status, "value") else str(f.status),
        }
        for f in facts
    ]

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
                        "translated_value": {"type": "object"},
                    },
                },
            }
        },
        "required": ["translated_facts"],
    }

    request = StructuredRequest(
        task="translation_v1",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        json_schema=schema,
        context={"target_lang": target_lang},
    )

    try:
        raw_output = await provider.generate_structured(request)
        translated_items = raw_output.get("translated_facts", [])

        # Fallback for rule_based provider
        if provider.info.name == "rule_based" and not translated_items:
            lang_map = {
                "hi": "hi-IN",
                "gu": "gu-IN",
                "en": "en-GB",
                "mr": "mr-IN",
                "ta": "ta-IN",
                "te": "te-IN",
            }
            mapped_target = lang_map.get(target_lang, target_lang)
            translator = MyMemoryTranslator(source="en-GB", target=mapped_target)

            async def _translate(text: str) -> str:
                try:
                    res = await asyncio.to_thread(translator.translate, text)
                    return res if res else f"[{target_lang}] {text}"
                except Exception as ex:
                    logger.error(f"MyMemoryTranslator failed for text '{text}': {ex}")
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
                    "translated_value": trans_val,
                })

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
                    "status": original_fact.status,
                })

        result = {
            "case_id": case_id,
            "language": target_lang,
            "facts": final_facts,
        }
        _TRANSLATION_CACHE[cache_key] = result
        return result
    except Exception as e:
        logger.error(f"Translation failed for case_id={case_id}: {e}")
        raise e


async def auto_translate_on_summary_created(
    db: Session,
    case_id: str,
    target_langs: list[str] | None = None,
) -> None:
    """
    Hook executed when a discharge summary is created in the pipeline.
    Pre-warms translation cache for all supported regional languages:
    Hindi (hi), Gujarati (gu), Marathi (mr), Tamil (ta), Telugu (te).
    """
    if target_langs is None:
        target_langs = ["hi", "gu", "mr", "ta", "te"]

    google_key = get_settings().google_translate_api_key or os.environ.get("GOOGLE_TRANSLATE_API_KEY", "")
    if not google_key:
        logger.debug("auto_translate_on_summary_created skipped: GOOGLE_TRANSLATE_API_KEY not set.")
        return

    logger.info(f"Auto-translating summary for case_id={case_id} across {target_langs}...")
    for lang in target_langs:
        try:
            await translate_facts(db, case_id, lang)
            logger.debug(f"Auto-translated case_id={case_id} into {lang}")
        except Exception as err:
            logger.warning(f"Auto-translation on summary creation failed for lang={lang}: {err}")

