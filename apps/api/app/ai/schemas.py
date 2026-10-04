"""Structured extraction schema. Every candidate MUST carry a source reference (page + verbatim quote).

Values are typed per fact type via a discriminated union so malformed model output fails validation.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page_number: int = Field(ge=1)
    quote: str = Field(min_length=3, max_length=600, description="Verbatim text copied from the page")
    section: str | None = Field(default=None, max_length=120)


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: SourceRef
    legible: bool = Field(default=True, description="False when the source text cannot be read reliably")


class FollowUpValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: str | None = Field(default=None, description="ISO date YYYY-MM-DD, or null if not readable")
    time: str | None = None
    department: str | None = None
    clinician: str | None = None
    raw_text: str = Field(description="The date/time text exactly as written")

    @field_validator("date")
    @classmethod
    def _iso(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from datetime import date

        date.fromisoformat(v)
        return v


class MedicationValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=120)
    strength: str | None = None
    quantity: str | None = None
    frequency: str | None = None
    duration: str | None = None
    timing: str | None = None


class TextValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=2, max_length=400)


class AllergyValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    substance: str = Field(min_length=2, max_length=200)
    no_known_allergies: bool = False


class EncounterDateValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["admission", "discharge"]
    date: str | None = None
    raw_text: str


class FollowUpCandidate(_Base):
    fact_type: Literal["follow_up"]
    value: FollowUpValue


class MedicationCandidate(_Base):
    fact_type: Literal["medication"]
    value: MedicationValue


class InstructionCandidate(_Base):
    fact_type: Literal["instruction"]
    value: TextValue


class WarningSignCandidate(_Base):
    fact_type: Literal["warning_sign"]
    value: TextValue


class AllergyCandidate(_Base):
    fact_type: Literal["allergy"]
    value: AllergyValue


class ConditionCandidate(_Base):
    fact_type: Literal["documented_condition"]
    value: TextValue


class EncounterDateCandidate(_Base):
    fact_type: Literal["encounter_date"]
    value: EncounterDateValue


FactCandidate = Annotated[
    FollowUpCandidate
    | MedicationCandidate
    | InstructionCandidate
    | WarningSignCandidate
    | AllergyCandidate
    | ConditionCandidate
    | EncounterDateCandidate,
    Field(discriminator="fact_type"),
]


class ExtractionOutput(BaseModel):
    """What a provider must return for the `extraction_v1` task."""

    model_config = ConfigDict(extra="forbid")
    facts: list[FactCandidate] = Field(default_factory=list)
