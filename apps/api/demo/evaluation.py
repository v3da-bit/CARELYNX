"""Run the demo scenarios through the real API pipeline (upload → process → facts) and score them against each
scenario's `expected` labels. Shared by tests/evaluation/test_scenarios.py and scripts/evaluate_clinical.py.

Metrics (per scenario; overall = micro-average):
  precision          VERIFIED facts of labelled types that match a label / all such VERIFIED facts
  recall             labels found among presented (non-REJECTED) facts, any status
  evidence_correct   presented facts whose evidence is all verified verbatim / presented facts
  unsupported        VERIFIED facts lacking verified evidence (must be 0)
  conflict_recall    expected conflicting fact types that produced a conflict / expected types
  escalation_ok      (open reviews > 0) == expected review_required
  latency            wall time per document (upload + process)
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from sqlalchemy import func, select

from demo.fixtures import Scenario, render_pdf

_COUNTED = (("instruction", "instructions"), ("warning_sign", "warning_signs"))


def fact_key(fact_type: str, v: dict[str, Any]) -> str | None:
    from app.services.conflicts import normalize

    match fact_type:
        case "follow_up":
            return v.get("date")
        case "medication":
            return f"{str(v.get('name') or '').lower()}|{normalize(v.get('strength'))}"
        case "allergy":
            return str(v.get("substance") or "").lower()
        case "documented_condition":
            return str(v.get("text") or "").lower()
        case "encounter_date":
            return f"{v.get('kind')}|{v.get('date')}"
    return None


@dataclass
class ScenarioResult:
    key: str
    extracted_by: list[str]
    facts_presented: int
    facts_verified: int
    tp_precision: int = 0
    fp: int = 0
    tp_recall: int = 0
    fn: int = 0
    evidence_ok: int = 0
    unsupported: int = 0
    conflicts: int = 0
    conflicts_expected: int = 0
    conflict_types: list[str] = field(default_factory=list)
    conflict_recall: float | None = None
    open_reviews: int = 0
    escalation_ok: bool = False
    must_not_verify_violations: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    unexpected: list[str] = field(default_factory=list)
    latency_s: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def precision(self) -> float | None:  # None: nothing was claimed as VERIFIED (e.g. a bad scan)
        return self.tp_precision / (self.tp_precision + self.fp) if self.tp_precision + self.fp else None

    @property
    def recall(self) -> float:
        return self.tp_recall / (self.tp_recall + self.fn) if self.tp_recall + self.fn else 1.0

    @property
    def evidence_correct(self) -> float:
        return self.evidence_ok / self.facts_presented if self.facts_presented else 1.0

    @property
    def passed(self) -> bool:
        return (
            not self.errors
            and self.fp == 0
            and self.fn == 0
            and self.unsupported == 0
            and self.conflicts == self.conflicts_expected
            and self.conflict_recall in (None, 1.0)
            and self.escalation_ok
            and not self.must_not_verify_violations
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "precision": self.precision,
            "recall": self.recall,
            "evidence_correct": self.evidence_correct,
            "passed": self.passed,
        }


def run_scenario(client: Any, scenario: Scenario) -> ScenarioResult:
    """Upload + process every document of the scenario into one case via the HTTP API, then score it."""
    from app.db.session import SessionLocal
    from app.models.entities import Conflict, ReviewCase
    from app.models.enums import ReviewStatus

    case_id: str | None = None
    latencies: list[float] = []
    errors: list[str] = []
    for doc in scenario.documents:
        pdf = render_pdf(doc)
        t0 = time.perf_counter()
        r = client.post(
            "/api/v1/documents",
            files={"file": (doc.filename, pdf, "application/pdf")},
            data={"case_id": case_id} if case_id else {},
        )
        if r.status_code != 201:
            errors.append(f"upload {doc.filename}: HTTP {r.status_code}")
            continue
        case_id = r.json()["case_id"]
        p = client.post(f"/api/v1/documents/{r.json()['id']}/process")
        latencies.append(time.perf_counter() - t0)
        if p.status_code != 200 or p.json().get("status") == "FAILED":
            errors.append(f"process {doc.filename}: HTTP {p.status_code} {p.json().get('status', '')}")

    if case_id is None:
        return score(scenario, [], 0, [], 0, latencies, errors)
    facts: list[dict[str, Any]] = client.get(f"/api/v1/cases/{case_id}/facts").json()
    cid = uuid.UUID(case_id)
    with SessionLocal() as db:
        conflicts = db.scalars(select(Conflict).where(Conflict.case_id == cid)).all()
        conflict_types = sorted({c.fact_type.value for c in conflicts})
        open_reviews = db.scalar(
            select(func.count())
            .select_from(ReviewCase)
            .where(ReviewCase.case_id == cid, ReviewCase.status == ReviewStatus.OPEN)
        )
    return score(scenario, facts, len(conflicts), conflict_types, open_reviews or 0, latencies, errors)


def score(
    scenario: Scenario,
    facts: list[dict[str, Any]],
    n_conflicts: int,
    conflict_types: list[str],
    open_reviews: int,
    latencies: list[float],
    errors: list[str],
) -> ScenarioResult:
    exp = scenario.expected
    presented = [f for f in facts if f["status"] != "REJECTED"]
    verified = [f for f in presented if f["status"] == "VERIFIED"]

    def ev_ok(f: dict[str, Any]) -> bool:
        return bool(f.get("evidence")) and all(e["verified"] for e in f["evidence"])

    res = ScenarioResult(
        key=scenario.key,
        extracted_by=sorted({f["extracted_by"] for f in facts}),
        facts_presented=len(presented),
        facts_verified=len(verified),
        evidence_ok=sum(ev_ok(f) for f in presented),
        unsupported=sum(not ev_ok(f) for f in verified),
        conflicts=n_conflicts,
        conflicts_expected=exp.get("conflicts", 0),
        conflict_types=conflict_types,
        open_reviews=open_reviews,
        escalation_ok=(open_reviews > 0) == exp.get("review_required", False),
        latency_s=[round(x, 4) for x in latencies],
        errors=errors,
    )

    labels: set[tuple[str, str]] = set(exp.get("facts", set()))
    labelled_types = {t for t, _ in labels}
    found = {(f["fact_type"], fact_key(f["fact_type"], f["value"])) for f in presented}
    claimed = {
        (f["fact_type"], fact_key(f["fact_type"], f["value"]))
        for f in verified
        if f["fact_type"] in labelled_types
    }
    res.tp_recall, res.fn = len(labels & found), len(labels - found)
    res.tp_precision, res.fp = len(claimed & labels), len(claimed - labels)
    res.missing = sorted(f"{t}:{k}" for t, k in labels - found)
    res.unexpected = sorted(f"{t}:{k}" for t, k in claimed - labels)

    for fact_type, label in _COUNTED:
        if label not in exp:
            continue
        n_exp = exp[label]
        n_pres = sum(f["fact_type"] == fact_type for f in presented)
        n_ver = sum(f["fact_type"] == fact_type for f in verified)
        res.tp_recall += min(n_pres, n_exp)
        res.fn += max(0, n_exp - n_pres)
        res.tp_precision += min(n_ver, n_exp)
        res.fp += max(0, n_ver - n_exp)

    expected_types = set(exp.get("conflicting_types", set()))
    if expected_types:
        res.conflict_recall = len(expected_types & set(conflict_types)) / len(expected_types)
    terms = {t.lower() for t in exp.get("must_not_verify", set())}
    res.must_not_verify_violations = sorted(
        f["fact_type"] for f in verified if any(t in json.dumps(f["value"]).lower() for t in terms)
    )
    return res


def overall(results: list[ScenarioResult]) -> dict[str, Any]:
    tp_p, fp = sum(r.tp_precision for r in results), sum(r.fp for r in results)
    tp_r, fn = sum(r.tp_recall for r in results), sum(r.fn for r in results)
    presented = sum(r.facts_presented for r in results)
    verified = sum(r.facts_verified for r in results)
    exp_c = [r for r in results if r.conflict_recall is not None]
    lat = [x for r in results for x in r.latency_s]
    return {
        "precision": tp_p / (tp_p + fp) if tp_p + fp else 1.0,
        "recall": tp_r / (tp_r + fn) if tp_r + fn else 1.0,
        "evidence_correct": sum(r.evidence_ok for r in results) / presented if presented else 1.0,
        "unsupported_claim_rate": sum(r.unsupported for r in results) / verified if verified else 0.0,
        "conflict_recall": sum(r.conflict_recall or 0 for r in exp_c) / len(exp_c) if exp_c else None,
        "escalation_correct": sum(r.escalation_ok for r in results) / len(results) if results else 1.0,
        "latency_mean_s": sum(lat) / len(lat) if lat else None,
        "latency_max_s": max(lat) if lat else None,
        "documents": len(lat),
        "passed": all(r.passed for r in results),
    }
