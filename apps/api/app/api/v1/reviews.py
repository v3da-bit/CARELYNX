"""Clinical review endpoints (reviewer bearer key required). Logic lives in app.services.reviews."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_reviewer
from app.db.session import get_db
from app.models import ReviewCase
from app.models.enums import ReviewStatus
from app.schemas.review import ResolveReviewRequest, ReviewCaseResponse, ReviewDetail
from app.services import reviews as review_service

router = APIRouter(prefix="/reviews", tags=["reviews"], dependencies=[Depends(require_reviewer)])


@router.get("", response_model=list[ReviewCaseResponse])
def list_reviews(
    status: ReviewStatus = Query(default=ReviewStatus.OPEN), db: Session = Depends(get_db)
) -> list[ReviewCase]:
    return review_service.list_reviews(db, status)


@router.get("/{review_id}", response_model=ReviewDetail)
def get_review(review_id: uuid.UUID, db: Session = Depends(get_db)) -> ReviewDetail:
    return review_service.review_detail(db, review_service.get_review(db, review_id))


@router.post("/{review_id}/resolve", response_model=ReviewCaseResponse)
def resolve_review(
    review_id: uuid.UUID,
    body: ResolveReviewRequest,
    db: Session = Depends(get_db),
) -> ReviewCase:
    return review_service.resolve_review(db, review_id, body, reviewer=body.reviewer_id)
