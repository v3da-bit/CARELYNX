"""Patient-facing care plan schema (API_CONTRACTS.md §3 `GET /cases/{id}/care-plan`)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.enums import Language
from app.schemas.document import CaseCounts
from app.schemas.fact import FactWithEvidence

TranslationStatus = Literal["source", "translated", "pending_review", "unavailable"]


class CarePlanDisplay(BaseModel):
    """Server-side formatting. A field absent from the source is null — never a placeholder."""

    title: str | None = None
    subtitle: str | None = None
    date: str | None = None


class CarePlanItem(FactWithEvidence):
    display: CarePlanDisplay
    translation_status: TranslationStatus


class CarePlanSections(BaseModel):
    follow_ups: list[CarePlanItem] = []
    medications: list[CarePlanItem] = []
    instructions: list[CarePlanItem] = []
    warning_signs: list[CarePlanItem] = []
    allergies: list[CarePlanItem] = []
    conditions: list[CarePlanItem] = []
    encounter_dates: list[CarePlanItem] = []


class CarePlanResponse(BaseModel):
    case_id: uuid.UUID
    language: Language
    generated_at: datetime
    counts: CaseCounts
    sections: CarePlanSections
