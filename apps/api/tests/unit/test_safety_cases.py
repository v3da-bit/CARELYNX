"""Safety policy, conflict detection and review severity (SAFETY.md §3, §6)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.entities import Case, Conflict, Fact, Patient, ReviewCase
from app.models.enums import FactStatus, FactType, ReviewReason, ReviewSeverity
from app.safety.policy import check_safety_policy, enforce_safety_on_fact
from app.services.conflicts import detect_conflicts
from app.services.extraction import review_severity


@pytest.mark.parametrize(
    "text",
    [
        "You should increase your dose to 20 mg",
        "I recommend switching to a stronger antibiotic",
        "Patient likely has diabetes based on symptoms",
        "Increase dose of aspirin",
        "The dosage should be doubled",
        "Substitute atorvastatin with rosuvastatin",
        "You probably have an infection",
    ],
)
def test_generated_advice_is_blocked(text: str) -> None:
    ok, violations = check_safety_policy({"text": text})
    assert not ok and violations


@pytest.mark.parametrize(
    "text",
    [
        "Stop the medication if a rash appears",
        "Do not drive for 24 hours",
        "Take medicines exactly as directed on this prescription",
        "Avoid heavy lifting",
        "Suspected pneumonia",
        "Do not alter dose or frequency without confirmation from the treating healthcare professional",
    ],
)
def test_documented_instructions_are_not_blocked(text: str) -> None:
    assert check_safety_policy({"text": text}) == (True, [])


def test_risky_phrase_inside_verified_quote_is_documented_not_generated() -> None:
    quote = "- Increase dose to 20 mg after 7 days"
    assert check_safety_policy({"text": "Increase dose to 20 mg after 7 days"}, source_quote=quote)[0]
    # The same phrase without (verified) source backing is model language → blocked.
    assert not check_safety_policy({"text": "Increase dose to 20 mg after 7 days"})[0]
    assert not check_safety_policy({"text": "You should increase dose"}, source_quote="Take 1 tablet daily")[
        0
    ]


def test_enforce_rejects_generated_diagnosis() -> None:
    fact = Fact(
        fact_type=FactType.DOCUMENTED_CONDITION,
        value={"text": "Patient likely has diabetes based on symptoms"},
        status=FactStatus.VERIFIED,
    )
    enforce_safety_on_fact(fact)
    assert fact.status == FactStatus.REJECTED and fact.status_reasons


@pytest.mark.parametrize(
    "ft", [FactType.ALLERGY, FactType.MEDICATION, FactType.FOLLOW_UP, FactType.WARNING_SIGN]
)
def test_high_risk_types_get_high_severity_reviews(ft: FactType) -> None:
    assert review_severity(ft, FactStatus.NEEDS_REVIEW) == ReviewSeverity.HIGH


def test_other_types_get_lower_severity() -> None:
    assert review_severity(FactType.INSTRUCTION, FactStatus.NEEDS_REVIEW) == ReviewSeverity.LOW
    assert review_severity(FactType.DOCUMENTED_CONDITION, FactStatus.HUMAN_REQUIRED) == ReviewSeverity.MEDIUM
    assert review_severity(FactType.INSTRUCTION, FactStatus.REJECTED) == ReviewSeverity.HIGH


# ───────────────────────── conflicts ─────────────────────────


def _case(db: Session) -> uuid.UUID:
    patient = Patient(id=uuid.uuid4())
    db.add(patient)
    db.flush()
    case = Case(id=uuid.uuid4(), patient_id=patient.id)
    db.add(case)
    db.flush()
    return case.id


def _fact(
    db: Session, case_id: uuid.UUID, ft: FactType, status: FactStatus = FactStatus.VERIFIED, **value
) -> Fact:
    f = Fact(case_id=case_id, fact_type=ft, value=value, status=status, status_reasons=[])
    db.add(f)
    db.flush()
    return f


def test_follow_up_date_conflict_opens_high_review(db: Session) -> None:
    cid = _case(db)
    a = _fact(db, cid, FactType.FOLLOW_UP, date="2026-10-14", department="Cardiology OPD")
    b = _fact(db, cid, FactType.FOLLOW_UP, date="2026-10-16", department="Cardiology")
    detect_conflicts(db, cid)
    assert a.status == b.status == FactStatus.CONFLICT_DETECTED
    review = db.query(ReviewCase).one()
    assert review.reason_code == ReviewReason.CONFLICT and review.severity == ReviewSeverity.HIGH
    assert set(review.fact_ids) == {str(a.id), str(b.id)}


def test_two_different_drug_conflicts_are_both_raised_once(db: Session) -> None:
    cid = _case(db)
    _fact(db, cid, FactType.MEDICATION, name="Atorvastatin", strength="40 mg")
    _fact(db, cid, FactType.MEDICATION, name="Atorvastatin", strength="20 mg")
    _fact(db, cid, FactType.MEDICATION, name="Lisinopril", strength="10mg")
    _fact(db, cid, FactType.MEDICATION, name="Lisinopril", strength="20mg")
    detect_conflicts(db, cid)
    detect_conflicts(db, cid)  # re-running must not duplicate
    subjects = sorted(c.conflict_data["subject"] for c in db.query(Conflict).all())
    assert subjects == ["atorvastatin", "lisinopril"]
    assert db.query(ReviewCase).count() == 2


def test_wording_noise_is_not_a_conflict(db: Session) -> None:
    cid = _case(db)
    a = _fact(db, cid, FactType.MEDICATION, name="Aspirin", strength="75mg", frequency="Once  daily")
    _fact(db, cid, FactType.MEDICATION, name="aspirin", strength="75 mg", frequency="once daily")
    _fact(
        db, cid, FactType.MEDICATION, name="Aspirin", strength="75 mg", frequency=None
    )  # unstated ≠ different
    detect_conflicts(db, cid)
    assert db.query(Conflict).count() == 0 and a.status == FactStatus.VERIFIED


def test_human_required_is_not_downgraded_but_linked(db: Session) -> None:
    cid = _case(db)
    a = _fact(db, cid, FactType.FOLLOW_UP, date="2026-10-14")
    b = _fact(db, cid, FactType.FOLLOW_UP, FactStatus.HUMAN_REQUIRED, date="2026-10-16")
    detect_conflicts(db, cid)
    assert a.status == FactStatus.CONFLICT_DETECTED
    assert b.status == FactStatus.HUMAN_REQUIRED
    assert "Conflicting values detected across documents" in b.status_reasons
    assert str(b.id) in db.query(ReviewCase).one().fact_ids


def test_later_document_joins_open_conflict(db: Session) -> None:
    cid = _case(db)
    _fact(db, cid, FactType.FOLLOW_UP, date="2026-10-14")
    _fact(db, cid, FactType.FOLLOW_UP, date="2026-10-16")
    detect_conflicts(db, cid)
    c = _fact(db, cid, FactType.FOLLOW_UP, date="2026-10-18")
    detect_conflicts(db, cid)
    assert db.query(Conflict).count() == 1
    assert str(c.id) in db.query(ReviewCase).one().fact_ids
    assert c.status == FactStatus.CONFLICT_DETECTED
