import uuid
from typing import Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.enums import ReviewStatus, ReviewSeverity, ReviewReason, ReviewDecision

class ReviewCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    case_id: uuid.UUID
    reason: str
    reason_code: ReviewReason
    severity: ReviewSeverity
    status: ReviewStatus
    fact_ids: list[str]
    conflict_id: uuid.UUID | None
    document_id: uuid.UUID | None
    recommended_action: str
    decision: ReviewDecision | None
    resolved_by: str | None
    created_at: datetime
    resolved_at: datetime | None

class ResolveReviewRequest(BaseModel):
    decision: ReviewDecision
    resolution_notes: str | None = None
    reviewer_id: str
    
    # If resolving a conflict, specify which fact won (if any)
    winning_fact_id: uuid.UUID | None = None
