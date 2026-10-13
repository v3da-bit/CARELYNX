"""openai_compat provider with a mocked HTTP transport, and honest fallback provenance in run_extraction."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from app.ai.openai_compatible import OpenAICompatibleProvider
from app.ai.provider import ProviderError, StructuredRequest
from app.ai.schemas import ExtractionOutput
from app.services.extraction import run_extraction

PAGE = "DISCHARGE SUMMARY\nAllergies: Sulfa drugs\nDiagnosis: Unstable angina"
REQUEST = StructuredRequest(
    task="extraction_v1",
    system_prompt="sys",
    user_prompt="user",
    json_schema=ExtractionOutput.model_json_schema(),
    context={"pages": [{"page_number": 1, "text": PAGE}]},
)
GOOD = {
    "facts": [
        {
            "fact_type": "allergy",
            "legible": True,
            "source": {"page_number": 1, "quote": "Allergies: Sulfa drugs", "section": None},
            "value": {"substance": "Sulfa drugs", "no_known_allergies": False},
        }
    ]
}


def _provider(content: str | None = None, status: int = 200, exc: Exception | None = None):
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"], seen["body"] = request.url.path, json.loads(request.content)
        if exc:
            raise exc
        return httpx.Response(status, json={"choices": [{"message": {"content": content}}]})

    return OpenAICompatibleProvider(transport=httpx.MockTransport(handler)), seen


def test_success_returns_validated_facts_with_true_provenance() -> None:
    provider, seen = _provider(json.dumps(GOOD))
    output, extracted_by, fallback = asyncio.run(run_extraction(provider, REQUEST))
    assert extracted_by == "openai_compat" and fallback is None
    assert output.facts[0].value.substance == "Sulfa drugs"
    assert seen["path"].endswith("/v1/chat/completions")
    assert seen["body"]["response_format"]["type"] == "json_schema"


def test_fenced_json_is_accepted() -> None:
    provider, _ = _provider("```json\n" + json.dumps(GOOD) + "\n```")
    assert asyncio.run(provider.generate_structured(REQUEST)) == GOOD


@pytest.mark.parametrize(
    "kwargs",
    [
        {"content": "{not json"},  # malformed JSON
        {"content": json.dumps({"facts": [{"fact_type": "allergy"}]})},  # schema violation
        {"content": "[]"},  # non-object
        {"status": 500, "content": "x"},
        {"exc": httpx.ConnectError("down")},
    ],
)
def test_failure_falls_back_to_rule_based_honestly(kwargs) -> None:
    provider, _ = _provider(**kwargs)
    output, extracted_by, fallback = asyncio.run(run_extraction(provider, REQUEST))
    assert extracted_by == "rule_based (fallback from openai_compat)"
    assert fallback  # exception class name, recorded in the audit log
    assert {f.fact_type for f in output.facts} == {"allergy", "documented_condition"}


def test_provider_error_when_fallback_also_fails(monkeypatch) -> None:
    from app.ai import rule_based

    async def broken(self, request):
        raise RuntimeError("boom")

    monkeypatch.setattr(rule_based.RuleBasedProvider, "generate_structured", broken)
    provider, _ = _provider("{not json")
    with pytest.raises(ProviderError):
        asyncio.run(run_extraction(provider, REQUEST))


def test_provider_reports_configured_hardware_label() -> None:
    provider, _ = _provider("{}")
    assert provider.info.name == "openai_compat"
    # The label is whatever INFERENCE_HARDWARE_LABEL says (default "local-cpu"); never hardcoded to "AMD".
    from app.core.config import get_settings

    assert provider.info.hardware_label == get_settings().inference_hardware_label


def test_generate_text_errors_raise_instead_of_fake_text() -> None:
    provider, _ = _provider(exc=httpx.ReadTimeout("slow"))
    with pytest.raises(ProviderError):
        asyncio.run(provider.generate_text("s", "u"))
