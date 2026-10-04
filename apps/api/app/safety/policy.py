import re
from typing import Any

from app.models.enums import FactStatus, ReviewReason
from app.models.entities import Fact

# Keywords that indicate the model might be inventing or diagnosing rather than extracting.
FORBIDDEN_PATTERNS = [
    r"\b(diagnos(e|is)|suspect|suggests?|likely|probable|possible)\b",
    r"\b(increase|decrease|change|substitute|stop|start)\s+(dose|medication)\b",
    r"\b(go to (the )?er|emergency|urgent care|call 911)\b",
]

def check_safety_policy(fact_value: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Evaluates a fact value against the safety policy.
    Returns (is_safe, list of violation reasons).
    """
    violations = []
    
    # We serialize the value to string to check for patterns.
    # A more sophisticated approach would check specific fields.
    val_str = str(fact_value).lower()
    
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, val_str):
            violations.append(f"Contains forbidden safety pattern: {pattern}")
            
    return len(violations) == 0, violations

def enforce_safety_on_fact(fact: Fact) -> None:
    """Updates fact status if it violates safety policy."""
    is_safe, violations = check_safety_policy(fact.value)
    
    if not is_safe:
        fact.status = FactStatus.REJECTED
        fact.status_reasons = (fact.status_reasons or []) + violations
