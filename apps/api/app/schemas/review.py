"""Clinical review + audit API schemas (API_CONTRACTS.md §3, §6)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models.enums import (
    ActorType,
    ConflictStatus,
    FactType,
    ReviewDecision,
    ReviewReason,
    ReviewSeverity,
    ReviewStatus,
)
from app.schemas.fact import FactWithEvidence


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
    resolution: str | None
    resolved_by: str | None
    created_at: datetime
    resolved_at: datetime | None


class ConflictOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    fact_type: FactType
    conflict_data: dict[str, Any]
    status: ConflictStatus


class DocumentRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    filename: str


class ReviewDetail(ReviewCaseResponse):
    facts: list[FactWithEvidence]
    conflict: ConflictOut | None
    documents: list[DocumentRef]


class ResolveReviewRequest(BaseModel):
    decision: ReviewDecision
    resolution_notes: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    reviewer_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    winning_fact_id: uuid.UUID | None = None
    corrected_value: dict[str, Any] | None = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    event_type: str
    actor_type: ActorType
    actor_id: uuid.UUID | None
    metadata: dict[str, Any] = Field(validation_alias="event_metadata")
    created_at: datetime
