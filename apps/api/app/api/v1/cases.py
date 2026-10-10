"""Case endpoints."""

from sqlalchemy.dialects.postgresql import Any
# pyrefly: ignore [invalid-syntax]
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Fact, ReviewCase
from app.models.enums import FactStatus, ReviewStatus
from app.schemas.document import CaseCounts, CaseCreated, CaseOut, DocumentOut
from app.schemas.fact import FactResponse
from app.services import documents as doc_service

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseCreated, status_code=201)
def create_case(db: Session = Depends(get_db)) -> CaseCreated:
    case = doc_service.create_case(db)
    db.commit()
    return CaseCreated.model_validate(case)


def case_counts(db: Session, case_id: uuid.UUID) -> CaseCounts:
    rows = db.execute(
        select(Fact.status, func.count()).where(Fact.case_id == case_id).group_by(Fact.status)
    ).all()
    by_status = {status: n for status, n in rows}
    open_reviews = db.scalar(
        select(func.count())
        .select_from(ReviewCase)
        .where(ReviewCase.case_id == case_id, ReviewCase.status == ReviewStatus.OPEN)
    )
    return CaseCounts(
        verified=by_status.get(FactStatus.VERIFIED, 0),
        needs_review=by_status.get(FactStatus.NEEDS_REVIEW, 0),
        human_required=by_status.get(FactStatus.HUMAN_REQUIRED, 0),
        conflict_detected=by_status.get(FactStatus.CONFLICT_DETECTED, 0),
        rejected=by_status.get(FactStatus.REJECTED, 0),
        open_reviews=open_reviews or 0,
    )


@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: uuid.UUID, db: Session = Depends(get_db)) -> CaseOut:
    case = doc_service.get_case(db, case_id)
    return CaseOut(
        id=case.id,
        status=case.status,
        created_at=case.created_at,
        documents=[DocumentOut.model_validate(d) for d in case.documents],
        counts=case_counts(db, case.id),
    )

@router.get("/{case_id}/facts", response_model=list[FactResponse])
def get_case_facts(case_id: uuid.UUID, db: Session = Depends(get_db)) -> list[FactResponse]:
    case = doc_service.get_case(db, case_id)
    # pyrefly: ignore [bad-return]
    return db.scalars(
        select(Fact).where(Fact.case_id == case_id)
    ).all()

@router.post("/{case_id}/translate")
# pyrefly: ignore [not-a-type]
async def translate_case(case_id: uuid.UUID, target_lang: str, db: Session = Depends(get_db)) -> Any:
    case = doc_service.get_case(db, case_id)
    from app.services.translation import translate_facts
    result = await translate_facts(db, str(case_id), target_lang)
    return result

@router.get("/{case_id}/fhir")
# pyrefly: ignore [not-a-type]
def export_fhir(case_id: uuid.UUID, db: Session = Depends(get_db)) -> Any:
    """Mock FHIR Bundle Export for Phase 3 (Hospital Integration)"""
    case = doc_service.get_case(db, case_id)
    facts = db.scalars(select(Fact).where(Fact.case_id == case_id)).all()
    
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": str(case.patient_id) if case.patient_id else "unknown"
                }
            }
        ]
    }
    for fact in facts:
        if fact.fact_type == "medication":
            bundle["entry"].append({
                "resource": {
                    "resourceType": "MedicationStatement",
                    "id": str(fact.id),
                    "status": "active",
                    # pyrefly: ignore [bad-assignment]
                    "medicationCodeableConcept": {
                        "text": fact.value.get("name", "Unknown Medication")
                    }
                }
            })
    return bundle

@router.post("/{case_id}/reminders/sms")
def send_sms_reminders(case_id: uuid.UUID, phone: str, db: Session = Depends(get_db)) -> dict:
    """Mock Twilio SMS dispatcher for Phase 3 (Automated Reminders)"""
    case = doc_service.get_case(db, case_id)
    print(f"[TWILIO MOCK] Dispatching Care Plan SMS to {phone} for case {case.id}")
    return {"status": "dispatched", "phone": phone, "message": "Mock SMS sent successfully"}
