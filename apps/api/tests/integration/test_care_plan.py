"""GET /cases/{id}/care-plan (API_CONTRACTS §3), facts/evidence shape and FHIR export."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Document
from app.models.enums import FactStatus, FactType, Language
from app.services import documents as doc_service
from app.services import translation
from tests.integration.test_reviews import _fact

SECTIONS = {
    "follow_ups",
    "medications",
    "instructions",
    "warning_signs",
    "allergies",
    "conditions",
    "encounter_dates",
}


def seed(db: Session) -> str:
    case = doc_service.create_case(db)
    doc = Document(case_id=case.id, filename="A.pdf", mime_type="application/pdf", storage_key="a")
    db.add(doc)
    db.flush()
    v, nr, rej = FactStatus.VERIFIED, FactStatus.NEEDS_REVIEW, FactStatus.REJECTED
    _fact(db, case.id, doc, FactType.FOLLOW_UP, {"date": None, "raw_text": "1? Oct"}, nr)
    _fact(
        db,
        case.id,
        doc,
        FactType.FOLLOW_UP,
        {"date": "2026-10-16", "department": "Cardiology", "clinician": "Dr. Sharma", "raw_text": "16 Oct"},
        v,
    )
    _fact(db, case.id, doc, FactType.FOLLOW_UP, {"date": "2026-10-14", "raw_text": "14 Oct"}, v)
    _fact(
        db,
        case.id,
        doc,
        FactType.MEDICATION,
        {"name": "Aspirin", "strength": "75 mg", "frequency": "once daily", "timing": "after breakfast"},
        v,
    )
    _fact(db, case.id, doc, FactType.MEDICATION, {"name": "Metformin"}, nr)
    _fact(db, case.id, doc, FactType.MEDICATION, {"name": "Rejectedol", "strength": "5 mg"}, rej)
    _fact(db, case.id, doc, FactType.INSTRUCTION, {"text": "Rest at home for 7 days."}, v)
    _fact(db, case.id, doc, FactType.ALLERGY, {"substance": "none", "no_known_allergies": True}, v)
    _fact(
        db,
        case.id,
        doc,
        FactType.ENCOUNTER_DATE,
        {"kind": "discharge", "date": "2026-10-03", "raw_text": "x"},
        v,
    )
    db.commit()
    return str(case.id)


def _plan(client: TestClient, case_id: str, lang: str = "en") -> dict[str, Any]:
    r = client.get(f"/api/v1/cases/{case_id}/care-plan", params={"lang": lang})
    assert r.status_code == 200, r.text
    return r.json()


def test_care_plan_shape_sorting_and_display(client: TestClient, db: Session) -> None:
    case_id = seed(db)
    plan = _plan(client, case_id)
    assert plan["language"] == "en" and set(plan["sections"]) == SECTIONS
    assert plan["counts"]["rejected"] == 1
    s = plan["sections"]

    assert [i["display"]["date"] for i in s["follow_ups"]] == ["2026-10-14", "2026-10-16", None]
    assert s["follow_ups"][1]["display"] == {
        "title": "Follow-up appointment",
        "subtitle": "Cardiology · Dr. Sharma",
        "date": "2026-10-16",
    }
    assert s["follow_ups"][2]["status"] == "NEEDS_REVIEW"  # non-verified items still shown, with status

    meds = {m["display"]["title"]: m for m in s["medications"]}
    assert set(meds) == {"Aspirin", "Metformin"}  # REJECTED excluded
    assert meds["Aspirin"]["display"]["subtitle"] == "75 mg · once daily · after breakfast"
    assert meds["Metformin"]["display"]["subtitle"] is None  # never a placeholder
    assert meds["Aspirin"]["evidence"][0]["document_filename"] == "A.pdf"

    assert s["allergies"][0]["display"]["title"] == "No known allergies"
    assert s["encounter_dates"][0]["display"] == {
        "title": "Discharge date",
        "subtitle": None,
        "date": "2026-10-03",
    }
    assert s["instructions"][0]["display"]["title"] == "Rest at home for 7 days."
    assert {i["translation_status"] for sec in s.values() for i in sec} == {"source"}


def test_care_plan_translation(client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    case_id = seed(db)
    calls: list[tuple[list[str], Language, Sequence[str]]] = []

    async def fake(
        texts: list[str], target_lang: Language, protected_terms: Sequence[str] = ()
    ) -> list[str | None]:
        calls.append((list(texts), target_lang, tuple(protected_terms)))
        return [None if t == "Rest at home for 7 days." else f"HI[{t}]" for t in texts]

    monkeypatch.setattr(translation, "translate_texts", fake, raising=False)
    s = _plan(client, case_id, "hi")["sections"]

    assert len(calls) == 1
    texts, lang, protected = calls[0]
    assert lang == Language.HI and set(protected) == {"Aspirin", "Metformin"}
    assert "Aspirin" not in texts and "Metformin" not in texts  # drug names never sent
    assert "Cardiology · Dr. Sharma" in texts and "75 mg · once daily · after breakfast" in texts

    aspirin = next(m for m in s["medications"] if m["status"] == "VERIFIED")
    assert aspirin["display"]["title"] == "Aspirin" and aspirin["translation_status"] == "translated"
    assert aspirin["display"]["subtitle"] == "HI[75 mg · once daily · after breakfast]"
    fu = s["follow_ups"]
    assert (
        fu[0]["display"]["title"] == "HI[Follow-up appointment]" and fu[0]["display"]["date"] == "2026-10-14"
    )
    assert (
        fu[2]["translation_status"] == "pending_review"
        and fu[2]["display"]["title"] == "Follow-up appointment"
    )
    assert s["instructions"][0]["translation_status"] == "unavailable"
    assert s["instructions"][0]["display"]["title"] == "Rest at home for 7 days."


def test_care_plan_translation_engine_failure_degrades(client: TestClient, db: Session, monkeypatch) -> None:
    case_id = seed(db)

    async def boom(*_a: Any, **_k: Any) -> list[str | None]:
        raise RuntimeError("engine down")

    monkeypatch.setattr(translation, "translate_texts", boom, raising=False)
    s = _plan(client, case_id, "gu")["sections"]
    statuses = {i["translation_status"] for sec in s.values() for i in sec if i["status"] == "VERIFIED"}
    assert statuses == {"unavailable"}


def test_care_plan_rejects_unknown_language_and_case(client: TestClient, db: Session) -> None:
    case_id = seed(db)
    r = client.get(f"/api/v1/cases/{case_id}/care-plan", params={"lang": "fr"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    r = client.get("/api/v1/cases/00000000-0000-0000-0000-000000000000/care-plan")
    assert r.status_code == 404


def test_case_facts_with_evidence_and_fhir(client: TestClient, db: Session) -> None:
    case_id = seed(db)
    facts = client.get(f"/api/v1/cases/{case_id}/facts").json()
    assert len(facts) == 9
    ev = facts[0]["evidence"][0]
    assert ev["fact_id"] == facts[0]["id"] and ev["document_filename"] == "A.pdf"
    assert client.get(f"/api/v1/cases/{case_id}/facts").json() == facts  # deterministic order

    bundle = client.get(f"/api/v1/cases/{case_id}/fhir").json()
    meds = [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "MedicationStatement"]
    assert [m["medicationCodeableConcept"]["text"] for m in meds] == ["Aspirin"]  # VERIFIED only
    assert meds[0]["dosage"] == [{"text": "75 mg once daily after breakfast"}]


def test_case_created_has_timestamp(client: TestClient) -> None:
    body = client.post("/api/v1/cases").json()
    assert body["status"] == "OPEN" and body["created_at"]


def test_unhandled_error_is_sanitized_with_headers(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.main import create_app
    from app.services import care_plan

    case_id = seed(db)
    monkeypatch.setattr(
        care_plan, "case_facts", lambda *_: (_ for _ in ()).throw(RuntimeError("/secret/path"))
    )
    with TestClient(create_app(), raise_server_exceptions=False) as c:
        r = c.get(f"/api/v1/cases/{case_id}/care-plan")
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "INTERNAL_ERROR" and "secret" not in r.text
    assert r.headers["X-Request-ID"] == r.json()["error"]["request_id"]
    assert r.headers["X-Content-Type-Options"] == "nosniff"
