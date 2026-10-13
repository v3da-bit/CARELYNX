"""OpenAI-compatible chat-completions client (vLLM on AMD ROCm, or any /v1 endpoint).

This provider never falls back silently: any failure (network, HTTP error, non-JSON or non-object output)
raises
ProviderError. The extraction service decides whether to fall back to the rule-based extractor and records
that
fallback truthfully in `extracted_by` and the audit log (app.services.extraction).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.ai.provider import ProviderError, ProviderInfo, StructuredRequest
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _strip_fences(content: str) -> str:
    """Some models wrap JSON in ```json fences despite response_format; remove them, nothing else."""
    s = content.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else ""
        s = s.rsplit("```", 1)[0]
    return s.strip()


class OpenAICompatibleProvider:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        settings = get_settings()
        self.api_base = settings.inference_base_url
        self.api_key = settings.inference_api_key
        self.model = settings.inference_model
        self.timeout = settings.inference_timeout_s
        self._transport = transport  # injectable for tests
        # Label comes from INFERENCE_HARDWARE_LABEL and must describe where tokens were actually served.
        self.info = ProviderInfo(
            name="openai_compat", model=self.model, hardware_label=settings.inference_hardware_label
        )

    async def _chat(self, payload: dict[str, Any]) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            async with httpx.AsyncClient(
                base_url=self.api_base, headers=headers, transport=self._transport, timeout=self.timeout
            ) as client:
                response = await client.post("chat/completions", json={"model": self.model, **payload})
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"openai_compat request failed: {type(exc).__name__}") from exc
        if not isinstance(content, str):
            raise ProviderError("openai_compat returned no text content")
        return content

    async def generate_structured(self, request: StructuredRequest) -> dict[str, Any]:
        content = await self._chat(
            {
                "messages": [
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_prompt},
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": request.task, "schema": request.json_schema},
                },
                "temperature": 0.0,
            }
        )
        try:
            parsed = json.loads(_strip_fences(content))
        except json.JSONDecodeError as exc:
            raise ProviderError("openai_compat returned malformed JSON") from exc
        if not isinstance(parsed, dict):
            raise ProviderError("openai_compat returned non-object JSON")
        return parsed

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return await self._chat(
            {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.0,
            }
        )
