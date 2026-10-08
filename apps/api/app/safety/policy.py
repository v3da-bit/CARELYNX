import re
from typing import Any

from app.models.enums import FactStatus
from app.models.entities import Fact

# Patterns that indicate an unprompted model modification of clinical orders
# e.g., an LLM claiming it changed a dosage or recommended an unprescribed drug
FORBIDDEN_AUTONOMOUS_PATTERNS = [
    r"\b(i (recommend|suggest|prescribe|diagnose|altered|adjusted|changed))\b",
    r"\b(dosage (should be|was) (increased|decreased|modified))\b",
    r"\b(treatment (recommendation|advice):)\b",
]

def check_safety_policy(fact_value: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Evaluates a fact value against the safety policy.
    Returns (is_safe, list of violation reasons).
    """
    violations = []
    val_str = str(fact_value).lower()
    
    for pattern in FORBIDDEN_AUTONOMOUS_PATTERNS:
        if re.search(pattern, val_str):
            violations.append(f"Contains prohibited autonomous medical claim: {pattern}")
            
    return len(violations) == 0, violations

def enforce_safety_on_fact(fact: Fact) -> None:
    """Updates fact status if it violates safety policy."""
    is_safe, violations = check_safety_policy(fact.value)
    
    if not is_safe:
        fact.status = FactStatus.REJECTED
        fact.status_reasons = (fact.status_reasons or []) + violations

