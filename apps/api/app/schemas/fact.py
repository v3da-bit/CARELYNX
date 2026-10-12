"""Fact / evidence API schemas (API_CONTRACTS.md §5)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import FactStatus, FactType


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    fact_id: uuid.UUID
    document_id: uuid.UUID
    document_filename: str
    page_number: int
    section: str | None
    snippet: str | None
    char_start: int | None
    char_end: int | None
    verified: bool


class FactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    case_id: uuid.UUID
    fact_type: FactType
    value: dict[str, Any]
    status: FactStatus
    confidence: float | None
    status_reasons: list[Any]
    extracted_by: str
    human_verified: bool
    created_at: datetime
    updated_at: datetime


class FactWithEvidence(FactResponse):
    evidence: list[EvidenceResponse]
