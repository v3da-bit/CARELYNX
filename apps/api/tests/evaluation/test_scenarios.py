"""Scenarios A/B/C (CLAUDE.md §11) end-to-end through the real pipeline, scored against `expected` labels."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from demo.evaluation import run_scenario
from demo.fixtures import SCENARIOS


@pytest.mark.parametrize("key", sorted(SCENARIOS))
def test_scenario_matches_expected(client: TestClient, key: str) -> None:
    r = run_scenario(client, SCENARIOS[key])
    detail = r.as_dict()
    assert not r.errors, detail
    assert r.missing == [] and r.fn == 0, detail
    assert r.unexpected == [] and r.fp == 0, detail
    assert r.unsupported == 0, detail
    assert r.conflicts == SCENARIOS[key].expected["conflicts"], detail
    assert r.conflict_recall in (None, 1.0), detail
    assert r.escalation_ok, detail
    assert r.must_not_verify_violations == [], detail
    assert r.extracted_by == ["rule_based"], detail


def test_scenario_a_is_fully_verified(client: TestClient) -> None:
    r = run_scenario(client, SCENARIOS["A"])
    assert r.facts_verified == r.facts_presented and r.open_reviews == 0


def test_scenario_b_never_verifies_unreadable_text(client: TestClient) -> None:
    r = run_scenario(client, SCENARIOS["B"])
    assert r.facts_verified == 0 and r.open_reviews >= 1


def test_scenario_c_conflicts_are_follow_up_and_medication(client: TestClient) -> None:
    r = run_scenario(client, SCENARIOS["C"])
    assert r.conflict_types == ["follow_up", "medication"]


REPO_ROOT = Path(__file__).resolve().parents[4]


def _process_files(client: TestClient, *names: str) -> tuple[list[dict], list[dict]]:
    case_id = None
    for name in names:
        data = (REPO_ROOT / name).read_bytes()
        r = client.post(
            "/api/v1/documents",
            files={"file": (name, data, "application/pdf")},
            data={"case_id": case_id} if case_id else {},
        )
        assert r.status_code == 201, r.text
        case_id = r.json()["case_id"]
        assert client.post(f"/api/v1/documents/{r.json()['id']}/process").status_code == 200
    facts = client.get(f"/api/v1/cases/{case_id}/facts").json()
    reviews = [
        x
        for x in client.get("/api/v1/reviews", headers={"X-Carelynx-Role": "reviewer"}).json()
        if x["case_id"] == case_id
    ]
    return facts, reviews


def test_repo_sample_record_yields_sensible_verified_facts(client: TestClient) -> None:
    facts, reviews = _process_files(client, "sample_medical_record.pdf")
    by_type: dict[str, list] = {}
    for f in facts:
        by_type.setdefault(f["fact_type"], []).append(f)
    assert {f["value"]["name"] for f in by_type["medication"]} == {
        "Azithromycin",
        "Lisinopril",
        "Acetaminophen",
    }
    assert sorted(f["value"]["date"] for f in by_type["follow_up"]) == ["2026-10-14", "2026-10-16"]
    assert len(by_type["warning_sign"]) == 2 and len(by_type["instruction"]) == 3
    assert all(f["status"] == "VERIFIED" for f in facts) and reviews == []


@pytest.mark.parametrize(
    "second", ["sample_conflicting_prescription.pdf", "sample_prescription_conflict.pdf"]
)
def test_repo_conflict_samples_still_conflict(client: TestClient, second: str) -> None:
    facts, reviews = _process_files(client, "sample_medical_record.pdf", second)
    conflict_reviews = [r for r in reviews if r["reason_code"] == "CONFLICT"]
    assert len(conflict_reviews) == 2 and all(r["severity"] == "HIGH" for r in conflict_reviews)
    lisinopril = [f for f in facts if f["value"].get("name") == "Lisinopril"]
    assert {f["status"] for f in lisinopril} == {"CONFLICT_DETECTED"}
