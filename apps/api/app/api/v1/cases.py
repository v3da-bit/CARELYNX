"""Case endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_optional_user
from app.core.security import require_reviewer
from app.db.session import get_db
from app.models import AuditLog, Fact, User
from app.models.enums import FactStatus, FactType, Language
from app.schemas.care_plan import CarePlanResponse
from app.schemas.document import CaseCreated, CaseOut, DocumentOut
from app.schemas.fact import FactWithEvidence
from app.schemas.review import AuditLogOut
from app.services import care_plan
from app.services import documents as doc_service

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseCreated, status_code=201)
def create_case(
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CaseCreated:
    user_id = user.id if user else None
    case = doc_service.create_case(db, user_id=user_id)
    db.commit()
    return CaseCreated.model_validate(case)


@router.get("", response_model=list[CaseOut])
def list_cases(
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CaseOut]:
    """Returns cases for the authenticated user, or recent cases for reviewers."""
    if user is None:
        # Prevent open database exposure: unauthenticated visitors have no cases
        return []
    user_id = user.id if getattr(user, "role", "patient") not in ("reviewer", "admin") else None
    cases = doc_service.list_user_cases(db, user_id=user_id)
    return [
        CaseOut(
            id=c.id,
            status=c.status,
            created_at=c.created_at,
            documents=[DocumentOut.model_validate(d) for d in c.documents],
            counts=care_plan.case_counts(db, c.id),
        )
        for c in cases
    ]


@router.get("/{case_id}", response_model=CaseOut)
def get_case(
    case_id: uuid.UUID,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CaseOut:
    case = doc_service.get_case(db, case_id, user=user)
    return CaseOut(
        id=case.id,
        status=case.status,
        created_at=case.created_at,
        documents=[DocumentOut.model_validate(d) for d in case.documents],
        counts=care_plan.case_counts(db, case.id),
    )


@router.get("/{case_id}/facts", response_model=list[FactWithEvidence])
def get_case_facts(
    case_id: uuid.UUID,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[Fact]:
    doc_service.get_case(db, case_id, user=user)
    return care_plan.case_facts(db, case_id)


@router.get("/{case_id}/care-plan", response_model=CarePlanResponse)
async def get_care_plan(
    case_id: uuid.UUID,
    lang: Language = Query(default=Language.EN),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CarePlanResponse:
    doc_service.get_case(db, case_id, user=user)
    return await care_plan.build_care_plan(db, case_id, lang)


@router.get("/{case_id}/audit", response_model=list[AuditLogOut], dependencies=[Depends(require_reviewer)])
def get_case_audit(
    case_id: uuid.UUID,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[AuditLog]:
    doc_service.get_case(db, case_id, user=user)
    return list(
        db.scalars(
            select(AuditLog)
            .where(AuditLog.case_id == case_id)
            .order_by(AuditLog.created_at.desc(), AuditLog.id)
        ).all()
    )


@router.get("/{case_id}/fhir")
def export_fhir(case_id: uuid.UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Demo FHIR R4 Bundle of VERIFIED medication facts. Not a certified FHIR interface."""
    case = doc_service.get_case(db, case_id)
    patient_ref = {"reference": f"Patient/{case.patient_id}"} if case.patient_id else None
    entries: list[dict[str, Any]] = []
    if patient_ref:
        entries.append({"resource": {"resourceType": "Patient", "id": str(case.patient_id)}})
    meds = db.scalars(
        select(Fact)
        .where(
            Fact.case_id == case_id,
            Fact.fact_type == FactType.MEDICATION,
            Fact.status == FactStatus.VERIFIED,
        )
        .order_by(Fact.created_at, Fact.id)
    ).all()
    for fact in meds:
        v = fact.value or {}
        if not v.get("name"):
            continue  # never emit a placeholder drug name
        resource: dict[str, Any] = {
            "resourceType": "MedicationStatement",
            "id": str(fact.id),
            "status": "unknown",  # the document lists it; CARELYNX does not know whether it is being taken
            "medicationCodeableConcept": {"text": v["name"]},
        }
        if patient_ref:
            resource["subject"] = patient_ref
        dosage = " ".join(str(v[k]) for k in ("strength", "frequency", "timing", "duration") if v.get(k))
        if dosage:
            resource["dosage"] = [{"text": dosage}]
        entries.append({"resource": resource})
    return {"resourceType": "Bundle", "type": "collection", "entry": entries}
