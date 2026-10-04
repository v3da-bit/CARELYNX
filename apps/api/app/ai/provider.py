"""InferenceProvider abstraction (CLAUDE.md §4). Business logic depends only on this protocol.

Providers return *raw* output. Validation (Pydantic → safety → evidence) is always done by application code,
never trusted to the provider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class PageInput:
    page_number: int
    text: str


@dataclass(frozen=True)
class StructuredRequest:
    task: str  # e.g. "extraction_v1"
    system_prompt: str
    user_prompt: str
    json_schema: dict[str, Any]
    context: dict[str, Any] = field(default_factory=dict)  # structured inputs (e.g. pages)


@dataclass(frozen=True)
class ProviderInfo:
    name: str
    model: str
    hardware_label: str


class InferenceProvider(Protocol):
    info: ProviderInfo

    async def generate_structured(self, request: StructuredRequest) -> dict[str, Any]:
        """Return the raw JSON object produced for the request. Caller validates it."""
        ...

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str: ...


class ProviderError(RuntimeError):
    """Raised when a provider cannot produce output (network, timeout, malformed JSON)."""
