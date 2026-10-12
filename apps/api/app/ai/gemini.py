import json
import logging
import os
import re
from typing import Any

import httpx

from app.ai.provider import InferenceProvider, ProviderInfo, StructuredRequest
from app.ai.rule_based import RuleBasedProvider
from app.core.config import get_settings

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _clean_json_markdown(text: str) -> str:
    """Strip markdown codeblock wrappers if present in model output."""
    trimmed = text.strip()
    if trimmed.startswith("```"):
        trimmed = re.sub(r"^```(?:json)?\s*", "", trimmed, flags=re.IGNORECASE)
        trimmed = re.sub(r"\s*```$", "", trimmed)
    return trimmed.strip()


class GeminiProvider(InferenceProvider):
    """Direct Google Gemini inference provider for clinical extraction and patient-friendly simplification.

    Reads API key from .env (GEMINI_API_KEY or INFERENCE_API_KEY).
    Uses Gemini 1.5 Flash structured output mode.
    Falls back gracefully to RuleBasedProvider on offline/invalid credentials.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = (
            getattr(settings, "gemini_api_key", "")
            or getattr(settings, "inference_api_key", "")
            or os.environ.get("GEMINI_API_KEY", "")
            or os.environ.get("INFERENCE_API_KEY", "")
        ).strip()
        self.model = getattr(settings, "inference_model", "gemini-1.5-flash") or "gemini-1.5-flash"
        # Standardize model string if OpenAI style was passed
        if "gemini" in self.model.lower() and "/" in self.model:
            self.model = self.model.split("/")[-1]
        elif not self.model or "qwen" in self.model.lower() or "llama" in self.model.lower():
            self.model = "gemini-1.5-flash"
        self.timeout = float(getattr(settings, "inference_timeout_s", 60.0) or 60.0)
        self.hardware_label = getattr(settings, "inference_hardware_label", "gemini-cloud")

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="gemini",
            model=self.model,
            hardware_label=self.hardware_label,
        )

    async def generate_structured(self, request: StructuredRequest) -> dict[str, Any]:
        """Calls Gemini with strict JSON mode, falling back to rule-based on failure."""
        if not self.api_key:
            logger.info("No Gemini API key configured; using RuleBasedProvider fallback.")
            return await RuleBasedProvider().generate_structured(request)

        url = f"{GEMINI_API_BASE}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": request.user_prompt}],
                }
            ],
            "systemInstruction": {
                "parts": [{"text": request.system_prompt}],
            },
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                resp.raise_for_status()
                data = resp.json()

            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("Gemini returned empty candidate list")

            text_part = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            cleaned = _clean_json_markdown(text_part)
            parsed = json.loads(cleaned)
            if not isinstance(parsed, dict):
                raise ValueError(f"Gemini returned non-dict JSON: {type(parsed)}")
            return parsed

        except Exception as exc:
            logger.warning(
                "Gemini inference failed (will use RuleBasedProvider fallback): %s", exc
            )
            fallback = RuleBasedProvider()
            return await fallback.generate_structured(request)

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """Text generation endpoint with RuleBasedProvider fallback."""
        if not self.api_key:
            return await RuleBasedProvider().generate_text(system_prompt, user_prompt)

        url = f"{GEMINI_API_BASE}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt}],
            },
            "generationConfig": {
                "temperature": 0.0,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                resp.raise_for_status()
                data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("Gemini returned empty candidate list")
            return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        except Exception as exc:
            logger.warning("Gemini text generation failed: %s", exc)
            return await RuleBasedProvider().generate_text(system_prompt, user_prompt)
