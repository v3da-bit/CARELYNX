import uuid
from typing import Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import ReviewCase, Fact, Conflict
from app.models.enums import ReviewStatus, FactStatus, ConflictStatus, ActorType, AuditEvent
from app.schemas.review import ReviewCaseResponse, ResolveReviewRequest
from app.services import audit
from app.core.security import require_reviewer

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
    dependencies=[Depends(require_reviewer)]
)

@router.get("", response_model=list[ReviewCaseResponse])
def get_open_reviews(db: Session = Depends(get_db)) -> Any:
    return db.scalars(
        select(ReviewCase)
        .where(ReviewCase.status == ReviewStatus.OPEN)
        .order_by(ReviewCase.created_at.desc())
    ).all()

@router.get("/{review_id}", response_model=ReviewCaseResponse)
def get_review(review_id: uuid.UUID, db: Session = Depends(get_db)) -> Any:
    review = db.get(ReviewCase, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review case not found")
    return review

@router.post("/{review_id}/resolve", response_model=ReviewCaseResponse)
def resolve_review(
    review_id: uuid.UUID, 
    request: ResolveReviewRequest,
    db: Session = Depends(get_db)
) -> Any:
    review = db.get(ReviewCase, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review case not found")
        
    if review.status != ReviewStatus.OPEN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review case already resolved")
        
    review.status = ReviewStatus.RESOLVED
    review.decision = request.decision
    review.resolution = request.resolution_notes
    review.resolved_by = request.reviewer_id
    from app.db.base import utcnow
    review.resolved_at = utcnow()
    
    # Update facts based on resolution
    fact_ids = [uuid.UUID(f_id) for f_id in review.fact_ids]
    facts = db.scalars(select(Fact).where(Fact.id.in_(fact_ids))).all()
    
    for fact in facts:
        fact.human_verified = True
        # Simplified: If they approved a conflict, we check which fact won
        if review.conflict_id:
            if request.winning_fact_id and fact.id == request.winning_fact_id:
                fact.status = FactStatus.VERIFIED
            else:
                fact.status = FactStatus.REJECTED
                fact.status_reasons = fact.status_reasons + ["Rejected in conflict resolution"]
        else:
            # If not a conflict, just standard review
            if request.decision.value == "approve":
                fact.status = FactStatus.VERIFIED
            else:
                fact.status = FactStatus.REJECTED
    
    # Resolve the conflict if there is one
    if review.conflict_id:
        conflict = db.get(Conflict, review.conflict_id)
        if conflict:
            conflict.status = ConflictStatus.RESOLVED
            conflict.resolved_at = utcnow()
            
    db.commit()
    db.refresh(review)
    
    audit.record(
        db,
        AuditEvent.REVIEW_RESOLVED,
        actor_type=ActorType.REVIEWER,
        # pyrefly: ignore [bad-argument-type]
        actor_id=request.reviewer_id,
        case_id=review.case_id,
        review_id=str(review.id)
    )
    
    return review
