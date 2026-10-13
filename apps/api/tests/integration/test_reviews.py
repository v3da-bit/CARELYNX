"""Reviewer auth, review decisions (API_CONTRACTS §6) and audit trail."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import AuditLog, Conflict, Document, Evidence, Fact, ReviewCase
from app.models.enums import (
    ConflictStatus,
    FactStatus,
    FactType,
    ReviewReason,
    ReviewSeverity,
)
from app.services import documents as doc_service
from tests.conftest import REVIEWER

NOTES = "Checked against the original document."


def _fact(
    db: Session,
    case_id: uuid.UUID,
    doc: Document,
    ftype: FactType,
    value: dict[str, Any],
    status: FactStatus,
    page: int = 1,
) -> Fact:
    f = Fact(
        case_id=case_id,
        fact_type=ftype,
        value=value,
        status=status,
        confidence=1.0,
        extracted_by="rule_based",
    )
    f.evidence.append(Evidence(document_id=doc.id, page_number=page, snippet=str(value), verified=True))
    db.add(f)
    db.flush()
    return f


def seed(db: Session) -> dict[str, Any]:
    """A case with one single-fact review and one two-fact conflict review."""
    case = doc_service.create_case(db)
    doc_a = Document(case_id=case.id, filename="A_summary.pdf", mime_type="application/pdf", storage_key="a")
    doc_b = Document(case_id=case.id, filename="B_letter.pdf", mime_type="application/pdf", storage_key="b")
    db.add_all([doc_a, doc_b])
    db.flush()
    med = _fact(
        db,
        case.id,
        doc_a,
        FactType.MEDICATION,
        {"name": "Aspirin", "strength": "75 mg"},
        FactStatus.NEEDS_REVIEW,
    )
    fu_a = _fact(
        db,
        case.id,
        doc_a,
        FactType.FOLLOW_UP,
        {"date": "2026-10-14", "raw_text": "14 Oct 2026"},
        FactStatus.CONFLICT_DETECTED,
    )
    fu_b = _fact(
        db,
        case.id,
        doc_b,
        FactType.FOLLOW_UP,
        {"date": "2026-10-16", "raw_text": "16 Oct 2026"},
        FactStatus.CONFLICT_DETECTED,
    )
    conflict = Conflict(
        case_id=case.id,
        fact_type=FactType.FOLLOW_UP,
        conflict_data={"fact_ids": [str(fu_a.id), str(fu_b.id)]},
    )
    db.add(conflict)
    db.flush()
    single = ReviewCase(
        case_id=case.id,
        reason="Low quality",
        reason_code=ReviewReason.LOW_TEXT_QUALITY,
        severity=ReviewSeverity.MEDIUM,
        fact_ids=[str(med.id)],
        document_id=doc_a.id,
    )
    pair = ReviewCase(
        case_id=case.id,
        reason="Conflict",
        reason_code=ReviewReason.CONFLICT,
        severity=ReviewSeverity.HIGH,
        fact_ids=[str(fu_a.id), str(fu_b.id)],
        conflict_id=conflict.id,
    )
    db.add_all([single, pair])
    db.commit()
    return {
        "case": case.id,
        "med": med.id,
        "fu_a": fu_a.id,
        "fu_b": fu_b.id,
        "single": single.id,
        "pair": pair.id,
        "conflict": conflict.id,
    }


def _resolve(client: TestClient, review_id: uuid.UUID, headers: dict[str, str] = REVIEWER, **body: Any):
    body = {"resolution_notes": NOTES, "reviewer_id": "demo-reviewer", **body}
    return client.post(f"/api/v1/reviews/{review_id}/resolve", json=body, headers=headers)


def _status(db: Session, fid: uuid.UUID) -> FactStatus:
    db.expire_all()
    return db.get_one(Fact, fid).status


def test_reviewer_endpoints_require_reviewer_role(client: TestClient, db: Session) -> None:
    s = seed(db)
    for headers in ({}, {"X-Carelynx-Role": "patient"}, {"X-Carelynx-Role": "admin"}):
        for path in ("/api/v1/reviews", f"/api/v1/reviews/{s['single']}", f"/api/v1/cases/{s['case']}/audit"):
            r = client.get(path, headers=headers)
            assert r.status_code == 403, (path, headers)
            assert r.json()["error"]["code"] == "FORBIDDEN"
        assert _resolve(client, s["single"], headers=headers, decision="APPROVE").status_code == 403
    assert client.get("/api/v1/reviews", headers=REVIEWER).status_code == 200


def test_approve_single_fact_review_writes_audit(client: TestClient, db: Session) -> None:
    s = seed(db)
    r = _resolve(client, s["single"], decision="APPROVE")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "RESOLVED" and body["decision"] == "APPROVE"
    assert body["resolved_by"] == "demo-reviewer"
    assert body["resolution"] == NOTES
    assert _status(db, s["med"]) == FactStatus.VERIFIED
    assert db.get_one(Fact, s["med"]).human_verified

    rows = db.query(AuditLog).filter(AuditLog.event_type == "REVIEW_RESOLVED").all()
    assert len(rows) == 1
    meta = rows[0].event_metadata
    assert meta["reviewer"] == "demo-reviewer" and meta["decision"] == "APPROVE"
    assert meta["fact_ids"] == [str(s["med"])]
    assert rows[0].actor_type.value == "REVIEWER"

    again = _resolve(client, s["single"], decision="REJECT")
    assert again.status_code == 409 and again.json()["error"]["code"] == "INVALID_STATE"

    audit = client.get(f"/api/v1/cases/{s['case']}/audit", headers=REVIEWER).json()
    assert audit[0]["event_type"] == "REVIEW_RESOLVED"  # newest first
    assert audit[0]["metadata"]["decision"] == "APPROVE"


def test_decisions_that_do_not_fit_the_review(client: TestClient, db: Session) -> None:
    s = seed(db)
    cases = [
        (s["pair"], {"decision": "APPROVE"}),
        (s["single"], {"decision": "SELECT_SOURCE", "winning_fact_id": str(s["med"])}),
        (s["pair"], {"decision": "SELECT_SOURCE"}),
        (s["pair"], {"decision": "SELECT_SOURCE", "winning_fact_id": str(s["med"])}),  # not in fact_ids
        (
            s["pair"],
            {"decision": "CORRECT_VALUE", "corrected_value": {"raw_text": "x"}},
        ),  # 2 facts, no winner
    ]
    for review_id, body in cases:
        r = _resolve(client, review_id, **body)
        assert r.status_code == 409, (body, r.text)
        assert r.json()["error"]["code"] == "CONFLICT_ERROR"
    # nothing changed, nothing audited
    assert _status(db, s["fu_a"]) == FactStatus.CONFLICT_DETECTED
    assert db.query(AuditLog).filter(AuditLog.event_type == "REVIEW_RESOLVED").count() == 0


def test_resolution_notes_required(client: TestClient, db: Session) -> None:
    s = seed(db)
    for notes in (None, "", "   ", "x" * 2001):
        body: dict[str, Any] = {"decision": "REJECT", "reviewer_id": "demo-reviewer"}
        if notes is not None:
            body["resolution_notes"] = notes
        r = client.post(f"/api/v1/reviews/{s['single']}/resolve", json=body, headers=REVIEWER)
        assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_select_source_resolves_conflict(client: TestClient, db: Session) -> None:
    s = seed(db)
    r = _resolve(client, s["pair"], decision="SELECT_SOURCE", winning_fact_id=str(s["fu_a"]))
    assert r.status_code == 200, r.text
    assert _status(db, s["fu_a"]) == FactStatus.VERIFIED
    assert _status(db, s["fu_b"]) == FactStatus.REJECTED
    assert db.get_one(Conflict, s["conflict"]).status == ConflictStatus.RESOLVED


def test_reject_rejects_all(client: TestClient, db: Session) -> None:
    s = seed(db)
    assert _resolve(client, s["pair"], decision="REJECT").status_code == 200
    assert {_status(db, s["fu_a"]), _status(db, s["fu_b"])} == {FactStatus.REJECTED}


def test_correct_value(client: TestClient, db: Session) -> None:
    s = seed(db)
    r = _resolve(client, s["single"], decision="CORRECT_VALUE")
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    for bad in ({"name": "A"}, {"name": "Aspirin", "dose_change": "x"}, {"name": "Aspirin, increase dose"}):
        r = _resolve(client, s["single"], decision="CORRECT_VALUE", corrected_value=bad)
        assert r.status_code == 422, bad

    r = _resolve(
        client,
        s["single"],
        decision="CORRECT_VALUE",
        corrected_value={"name": "Aspirin", "strength": "150 mg"},
    )
    assert r.status_code == 200, r.text
    db.expire_all()
    fact = db.get_one(Fact, s["med"])
    assert fact.status == FactStatus.VERIFIED and fact.extracted_by == "human_review"
    assert fact.value["strength"] == "150 mg" and fact.value["frequency"] is None

    # conflict review: correct the winner, reject the other
    r = _resolve(
        client,
        s["pair"],
        decision="CORRECT_VALUE",
        winning_fact_id=str(s["fu_b"]),
        corrected_value={"date": "2026-10-15", "raw_text": "15 Oct 2026"},
    )
    assert r.status_code == 200, r.text
    assert _status(db, s["fu_b"]) == FactStatus.VERIFIED and _status(db, s["fu_a"]) == FactStatus.REJECTED


def test_list_filter_and_detail(client: TestClient, db: Session) -> None:
    s = seed(db)
    assert len(client.get("/api/v1/reviews", headers=REVIEWER).json()) == 2
    _resolve(client, s["single"], decision="REJECT")
    open_ = client.get("/api/v1/reviews?status=OPEN", headers=REVIEWER).json()
    resolved = client.get("/api/v1/reviews?status=RESOLVED", headers=REVIEWER).json()
    assert [r["id"] for r in open_] == [str(s["pair"])]
    assert [r["id"] for r in resolved] == [str(s["single"])]
    assert client.get("/api/v1/reviews?status=BOGUS", headers=REVIEWER).status_code == 422

    d = client.get(f"/api/v1/reviews/{s['pair']}", headers=REVIEWER).json()
    assert [f["id"] for f in d["facts"]] == [str(s["fu_a"]), str(s["fu_b"])]
    assert d["facts"][0]["evidence"][0]["document_filename"] == "A_summary.pdf"
    assert d["conflict"]["id"] == str(s["conflict"]) and d["conflict"]["status"] == "OPEN"
    assert {x["filename"] for x in d["documents"]} == {"A_summary.pdf", "B_letter.pdf"}
    single = client.get(f"/api/v1/reviews/{s['single']}", headers=REVIEWER).json()
    assert single["conflict"] is None and single["resolution"] == NOTES
    missing = client.get(f"/api/v1/reviews/{uuid.uuid4()}", headers=REVIEWER)
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "NOT_FOUND"
