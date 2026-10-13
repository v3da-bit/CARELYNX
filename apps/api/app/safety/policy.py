"""Safety policy (SAFETY.md §1, CLAUDE.md §7): block *generated* advice, dose changes and diagnoses.

Discharge documents legitimately contain instructions such as "stop the medication if a rash appears" or
"do not drive for 24 hours"; those are documented facts, not advice. The patterns below target the language of
an assistant giving advice ("you should increase your dose", "I recommend", "likely has … based on symptoms").
When a pattern matches text that is literally inside the verified source quote, it is the document speaking,
not
the model, so it is allowed through (it is still shown with its evidence).
"""

from __future__ import annotations

import re
from typing import Any

from app.models.entities import Fact
from app.models.enums import FactStatus

FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (label, re.compile(rx, re.I))
    for label, rx in (
        (
            "first-person recommendation",
            r"\b(?:i|we)\s+(?:would\s+)?(?:recommend|suggest|advise|prescribe|diagnose)\b",
        ),
        ("model-made order change", r"\b(?:i|we)\s+(?:have\s+)?(?:altered|adjusted|changed|modified)\b"),
        (
            "advice to change medication",
            r"\byou\s+should\s+(?:increase|decrease|reduce|double|halve|stop|start|skip|change|switch)\b",
        ),
        (
            "dose change",
            r"\b(?:increase|decrease|reduce|double|halve|adjust)\s+(?:the\s+|your\s+)?dos(?:e|age)\b",
        ),
        (
            "dose change",
            r"\bdos(?:e|age)\s+(?:should\s+be|was|has\s+been)\s+(?:increased|decreased|reduced|doubled|modified|changed)",
        ),
        ("medication substitution", r"\b(?:substitute|replace|swap)\b.{0,40}\b(?:with|for)\b"),
        ("treatment recommendation", r"\btreatment\s+(?:recommendation|advice)\b"),
        (
            "diagnosis",
            r"\b(?:likely|probably)\s+(?:has|have|suffers?)\b|\bbased\s+on\s+(?:your\s+|the\s+)?symptoms\b",
        ),
        ("diagnosis", r"\byou\s+(?:probably|likely|may|might)\s+have\b"),
    )
)


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in _strings(v)]
    return []


def check_safety_policy(
    fact_value: dict[str, Any], source_quote: str | None = None
) -> tuple[bool, list[str]]:
    """Return (is_safe, violations). `source_quote` must be a quote already verified verbatim on the page."""
    quote = (source_quote or "").lower()
    violations: list[str] = []
    for text in _strings(fact_value):
        for label, rx in FORBIDDEN_PATTERNS:
            for m in rx.finditer(text):
                if quote and m.group().lower() in quote:
                    continue  # documented in the source, not generated
                reason = f"Contains prohibited generated clinical language ({label})"
                if reason not in violations:
                    violations.append(reason)
    return not violations, violations


def enforce_safety_on_fact(fact: Fact) -> None:
    """Reject a fact whose value contains generated advice/diagnosis language."""
    is_safe, violations = check_safety_policy(fact.value)
    if not is_safe:
        fact.status = FactStatus.REJECTED
        fact.status_reasons = (fact.status_reasons or []) + violations
