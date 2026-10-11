import json
import logging

import httpx

from app.ai.provider import InferenceProvider, ProviderInfo, StructuredRequest
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(InferenceProvider):
    """OpenAI-compatible client for AMD ROCm vLLM, Gemini, or any /v1 endpoint.

    Hardware labels come from settings so the health/audit trail stays truthful.
    If the remote endpoint is down, extraction falls back to RuleBasedProvider
    (ARCHITECTURE §4) which still only extracts from the supplied page text.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.api_base = settings.inference_base_url
        self.api_key = settings.inference_api_key
        self.model = settings.inference_model
        self.timeout = settings.inference_timeout_s
        self.hardware_label = settings.inference_hardware_label
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        self.client = httpx.AsyncClient(base_url=self.api_base, headers=headers)

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="openai_compatible",
            model=self.model,
            hardware_label=self.hardware_label,
        )

    async def generate_structured(self, request: StructuredRequest) -> dict:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_output",
                    "schema": request.json_schema,
                },
            },
            "temperature": 0.0,
        }

        try:
            response = await self.client.post("/chat/completions", json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("Provider returned non-object JSON")
            return parsed
        except Exception as exc:
            logger.warning("OpenAI-compatible inference failed; falling back to RuleBasedProvider. Error: %s", exc)
            from app.ai.rule_based import RuleBasedProvider

            fallback = RuleBasedProvider()
            return await fallback.generate_structured(request)

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
        }
        try:
            response = await self.client.post("/chat/completions", json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.warning("OpenAI-compatible text generation failed; falling back to RuleBasedProvider. Error: %s", exc)
            from app.ai.rule_based import RuleBasedProvider

            fallback = RuleBasedProvider()
            return await fallback.generate_text(system_prompt, user_prompt)
