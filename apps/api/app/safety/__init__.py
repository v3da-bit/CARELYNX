"""Safety engine: verbatim evidence, deterministic status, and policy checks."""

from app.safety.evidence import EvidenceMatch, match_verbatim, match_verbatim_across_pages
from app.safety.policy import check_safety_policy, enforce_safety_on_fact
from app.safety.status import StatusDecision, compute_fact_status
from app.safety.text_quality import page_quality

__all__ = [
    "EvidenceMatch",
    "StatusDecision",
    "check_safety_policy",
    "compute_fact_status",
    "enforce_safety_on_fact",
    "match_verbatim",
    "match_verbatim_across_pages",
    "page_quality",
]
