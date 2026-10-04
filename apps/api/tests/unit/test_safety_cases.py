import uuid
import pytest
from sqlalchemy.orm import Session
from app.models.entities import Fact, Document, Case
from app.models.enums import FactType, FactStatus
from app.safety.policy import check_safety_policy, enforce_safety_on_fact
from app.services.conflicts import _check_fact_group_for_conflicts

def test_unsupported_medication_instruction_blocked():
    fact_val = {"name": "Lisinopril", "instruction": "start medication immediately"}
    is_safe, violations = check_safety_policy(fact_val)
    assert not is_safe
    assert len(violations) > 0

def test_conflicting_dates_review(db: Session):
    from app.models.entities import Patient, Case
    patient = Patient(id=uuid.uuid4())
    db.add(patient)
    db.flush()
    case_id = uuid.uuid4()
    c = Case(id=case_id, patient_id=patient.id)
    db.add(c)
    db.flush()

    f1 = Fact(id=uuid.uuid4(), case_id=case_id, fact_type=FactType.ENCOUNTER_DATE, value={"date": "2026-10-14", "kind": "follow_up"}, status=FactStatus.VERIFIED)
    f2 = Fact(id=uuid.uuid4(), case_id=case_id, fact_type=FactType.ENCOUNTER_DATE, value={"date": "2026-10-16", "kind": "follow_up"}, status=FactStatus.VERIFIED)
    db.add_all([f1, f2])
    db.flush()
    
    _check_fact_group_for_conflicts(db, case_id, FactType.ENCOUNTER_DATE, [f1, f2], "encounter_date_follow_up")
    
    # Assert statuses are changed
    assert f1.status == FactStatus.CONFLICT_DETECTED
    assert f2.status == FactStatus.CONFLICT_DETECTED

def test_low_ocr_confidence_review():
    # Tested by extraction logic (candidate.legible = False -> HUMAN_REQUIRED)
    pass

def test_missing_evidence_blocked():
    # Tested by extraction logic (verified = False -> HUMAN_REQUIRED)
    pass

def test_translation_of_uncertainty():
    # Will be tested in Phase 10
    pass

def test_llm_attempts_diagnosis_blocked():
    fact = Fact(
        fact_type=FactType.DOCUMENTED_CONDITION,
        value={"text": "Patient likely has diabetes based on symptoms"},
        status=FactStatus.VERIFIED
    )
    enforce_safety_on_fact(fact)
    assert fact.status == FactStatus.REJECTED
    assert len(fact.status_reasons) > 0

def test_llm_attempts_dose_change_blocked():
    fact = Fact(
        fact_type=FactType.MEDICATION,
        value={"name": "Aspirin", "timing": "increase dose"},
        status=FactStatus.VERIFIED
    )
    enforce_safety_on_fact(fact)
    assert fact.status == FactStatus.REJECTED

def test_reviewer_approval_audit():
    # Will be tested in Phase 9
    pass
