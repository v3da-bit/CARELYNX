"""Clinical review queue and resolution (API_CONTRACTS.md §6).

- APPROVE (non-conflict reviews): every fact VERIFIED.
- REJECT (any review): every fact REJECTED.
- SELECT_SOURCE (conflict reviews): winning_fact_id VERIFIED, the others REJECTED.
- CORRECT_VALUE (1-fact review, or winning_fact_id): target value := corrected_value, VERIFIED;
  others REJECTED.
All touched facts become human_verified. Resolution + REVIEW_RESOLVED audit row commit together.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai.schemas import AllergyValue, EncounterDateValue, FollowUpValue, MedicationValue, TextValue
from app.core.errors import AppError, ErrorCode
from app.db.base import utcnow
from app.models import Conflict, Document, Fact, ReviewCase
from app.models.enums import (
    ActorType,
    AuditEvent,
    ConflictStatus,
    FactStatus,
    FactType,
    ReviewDecision,
    ReviewReason,
    ReviewStatus,
)
from app.safety.policy import check_safety_policy
from app.schemas.fact import FactWithEvidence
from app.schemas.review import (
    ConflictOut,
    DocumentRef,
    ResolveReviewRequest,
    ReviewCaseResponse,
    ReviewDetail,
)
from app.services import audit

VALUE_MODELS: dict[FactType, type[BaseModel]] = {
    FactType.FOLLOW_UP: FollowUpValue,
    FactType.MEDICATION: MedicationValue,
    FactType.INSTRUCTION: TextValue,
    FactType.WARNING_SIGN: TextValue,
    FactType.DOCUMENTED_CONDITION: TextValue,
    FactType.ALLERGY: AllergyValue,
    FactType.ENCOUNTER_DATE: EncounterDateValue,
}


def list_reviews(db: Session, status: ReviewStatus) -> list[ReviewCase]:
    return list(
        db.scalars(
            select(ReviewCase)
            .where(ReviewCase.status == status)
            .order_by(ReviewCase.created_at.desc(), ReviewCase.id)
        ).all()
    )


def get_review(db: Session, review_id: uuid.UUID, *, for_update: bool = False) -> ReviewCase:
    stmt = select(ReviewCase).where(ReviewCase.id == review_id)
    review = db.scalar(stmt.with_for_update() if for_update else stmt)
    if review is None:
        raise AppError(ErrorCode.NOT_FOUND, "Review not found.", 404)
    return review


def _fact_uuids(review: ReviewCase) -> list[uuid.UUID]:
    return [uuid.UUID(str(x)) for x in review.fact_ids or []]


def _is_conflict(review: ReviewCase) -> bool:
    return review.conflict_id is not None or review.reason_code == ReviewReason.CONFLICT


def review_detail(db: Session, review: ReviewCase) -> ReviewDetail:
    ids = _fact_uuids(review)
    by_id = {
        f.id: f
        for f in db.scalars(select(Fact).where(Fact.id.in_(ids)).options(selectinload(Fact.evidence))).all()
    }
    facts = [by_id[i] for i in ids if i in by_id]
    doc_ids = list(dict.fromkeys([e.document_id for f in facts for e in f.evidence]))
    if review.document_id and review.document_id not in doc_ids:
        doc_ids.append(review.document_id)
    docs = {d.id: d for d in db.scalars(select(Document).where(Document.id.in_(doc_ids))).all()}
    conflict = db.get(Conflict, review.conflict_id) if review.conflict_id else None
    return ReviewDetail.model_validate(
        {
            **ReviewCaseResponse.model_validate(review).model_dump(),
            "facts": [FactWithEvidence.model_validate(f) for f in facts],
            "conflict": ConflictOut.model_validate(conflict) if conflict else None,
            "documents": [DocumentRef.model_validate(docs[i]) for i in doc_ids if i in docs],
        }
    )


def _reject_decision(message: str) -> AppError:
    return AppError(ErrorCode.CONFLICT_ERROR, message, 409)


def _validated_value(fact: Fact, corrected: dict[str, object] | None) -> dict[str, object]:
    if corrected is None:
        raise AppError(ErrorCode.VALIDATION_ERROR, "CORRECT_VALUE requires corrected_value.", 422)
    try:
        value = VALUE_MODELS[fact.fact_type].model_validate(corrected).model_dump()
    except ValidationError as exc:
        fields = ", ".join(".".join(str(p) for p in e["loc"]) or "value" for e in exc.errors()[:5])
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"corrected_value is invalid for {fact.fact_type.value}: {fields}",
            422,
        ) from exc
    # Same application-level policy as extraction: no dose changes / advice, even when typed by a human.
    safe, _ = check_safety_policy(value)
    if not safe:
        raise AppError(ErrorCode.VALIDATION_ERROR, "corrected_value violates the safety policy.", 422)
    return value


def resolve_review(
    db: Session, review_id: uuid.UUID, req: ResolveReviewRequest, *, reviewer: str
) -> ReviewCase:
    review = get_review(db, review_id, for_update=True)
    if review.status != ReviewStatus.OPEN:
        raise AppError(ErrorCode.INVALID_STATE, "Review is already resolved.", 409)

    ids = _fact_uuids(review)
    facts = {f.id: f for f in db.scalars(select(Fact).where(Fact.id.in_(ids))).all()}
    if req.winning_fact_id is not None and req.winning_fact_id not in ids:
        raise _reject_decision("winning_fact_id is not one of this review's facts.")
    conflict_review = _is_conflict(review)
    decision = req.decision

    verified: set[uuid.UUID] = set()
    if decision == ReviewDecision.APPROVE:
        if conflict_review:
            raise _reject_decision(
                "APPROVE is not allowed on a conflict review; use SELECT_SOURCE or REJECT."
            )
        verified = set(facts)
    elif decision == ReviewDecision.SELECT_SOURCE:
        if not conflict_review:
            raise _reject_decision("SELECT_SOURCE is only allowed on conflict reviews.")
        if req.winning_fact_id is None:
            raise _reject_decision("SELECT_SOURCE requires winning_fact_id.")
        if req.winning_fact_id not in facts:
            raise AppError(ErrorCode.NOT_FOUND, "Fact not found.", 404)
        verified = {req.winning_fact_id}
    elif decision == ReviewDecision.CORRECT_VALUE:
        target_id = req.winning_fact_id or (ids[0] if len(ids) == 1 else None)
        if target_id is None:
            raise _reject_decision("CORRECT_VALUE needs a single-fact review or a winning_fact_id.")
        if target_id not in facts:
            raise AppError(ErrorCode.NOT_FOUND, "Fact not found.", 404)
        target = facts[target_id]
        target.value = _validated_value(target, req.corrected_value)
        target.extracted_by = "human_review"
        verified = {target_id}
    # REJECT: verified stays empty → every fact REJECTED.

    now = utcnow()
    for fid, fact in facts.items():
        fact.status = FactStatus.VERIFIED if fid in verified else FactStatus.REJECTED
        fact.human_verified = True
        fact.status_reasons = [*(fact.status_reasons or []), f"Clinical review decision: {decision.value}"]

    review.status = ReviewStatus.RESOLVED
    review.decision = decision
    review.resolution = req.resolution_notes
    review.resolved_by = reviewer
    review.resolved_at = now
    if review.conflict_id:
        conflict = db.get(Conflict, review.conflict_id)
        if conflict is not None:
            conflict.status = ConflictStatus.RESOLVED
            conflict.resolved_at = now

    audit.record(
        db,
        AuditEvent.REVIEW_RESOLVED,
        actor_type=ActorType.REVIEWER,
        case_id=review.case_id,
        review_id=review.id,
        reviewer=reviewer,
        decision=decision.value,
        fact_ids=[str(i) for i in ids],
        winning_fact_id=req.winning_fact_id,
    )
    db.commit()
    return review
