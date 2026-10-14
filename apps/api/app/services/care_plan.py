"""Patient-facing care plan (API_CONTRACTS.md §3): grouping, display formatting, sorting and translation.

Formatting only re-arranges fields that exist in the stored fact value; it never invents data. Only VERIFIED
items are sent for translation, and drug names are never sent at all.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.base import utcnow
from app.models import Fact, ReviewCase
from app.models.enums import ActorType, AuditEvent, FactStatus, FactType, Language, ReviewStatus
from app.schemas.care_plan import (
    CarePlanDisplay,
    CarePlanItem,
    CarePlanResponse,
    CarePlanSections,
    TranslationStatus,
)
from app.schemas.document import CaseCounts
from app.schemas.fact import FactWithEvidence
from app.services import audit, translation
from app.services import documents as doc_service

logger = logging.getLogger("carelynx.care_plan")

SECTION_BY_TYPE: dict[FactType, str] = {
    FactType.FOLLOW_UP: "follow_ups",
    FactType.MEDICATION: "medications",
    FactType.INSTRUCTION: "instructions",
    FactType.WARNING_SIGN: "warning_signs",
    FactType.ALLERGY: "allergies",
    FactType.DOCUMENTED_CONDITION: "conditions",
    FactType.ENCOUNTER_DATE: "encounter_dates",
}
_DATE_SORTED = ("follow_ups", "encounter_dates")
_ENCOUNTER_TITLES = {"admission": "Admission date", "discharge": "Discharge date"}


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


def case_facts(db: Session, case_id: uuid.UUID) -> list[Fact]:
    """All facts of a case with evidence, in extraction order (deterministic)."""
    return list(
        db.scalars(
            select(Fact)
            .where(Fact.case_id == case_id)
            .options(selectinload(Fact.evidence))
            .order_by(Fact.created_at, Fact.id)
        ).all()
    )


def _s(value: dict[str, Any], key: str) -> str | None:
    v = value.get(key)
    if v is None or isinstance(v, bool):
        return None
    return str(v).strip() or None


def _join(value: dict[str, Any], *keys: str) -> str | None:
    return " · ".join(p for p in (_s(value, k) for k in keys) if p) or None


def display_for(fact: Fact) -> CarePlanDisplay:
    v = fact.value or {}
    simplified = _s(v, "simplified_meaning") or _s(v, "meaning") or _s(v, "explanation")
    match fact.fact_type:
        case FactType.FOLLOW_UP:
            return CarePlanDisplay(
                title="Follow-up appointment",
                subtitle=_join(v, "department", "clinician", "time"),
                date=_s(v, "date"),
                simplified_meaning=simplified,
            )
        case FactType.MEDICATION:
            return CarePlanDisplay(
                title=_s(v, "name"),
                subtitle=_join(v, "strength", "frequency", "timing", "duration", "quantity"),
                simplified_meaning=simplified,
            )
        case FactType.ALLERGY:
            return CarePlanDisplay(
                title="No known allergies" if v.get("no_known_allergies") is True else _s(v, "substance"),
                simplified_meaning=simplified,
            )
        case FactType.ENCOUNTER_DATE:
            return CarePlanDisplay(
                title=_ENCOUNTER_TITLES.get(str(v.get("kind"))),
                date=_s(v, "date"),
                simplified_meaning=simplified,
            )
        case _:
            return CarePlanDisplay(
                title=_s(v, "text"),
                simplified_meaning=simplified,
            )


def _translatable(fact: Fact, d: CarePlanDisplay) -> list[str]:
    """Field names of `display` to translate. Medication titles are drug names: never sent."""
    fields = (
        ["subtitle", "simplified_meaning"]
        if fact.fact_type == FactType.MEDICATION
        else ["title", "subtitle", "simplified_meaning"]
    )
    return [f for f in fields if getattr(d, f, None)]


async def build_care_plan(db: Session, case_id: uuid.UUID, lang: Language) -> CarePlanResponse:
    doc_service.get_case(db, case_id)
    facts = [f for f in case_facts(db, case_id) if f.status != FactStatus.REJECTED]
    displays = [display_for(f) for f in facts]
    statuses: list[TranslationStatus] = []

    if lang == Language.EN:
        statuses = ["source"] * len(facts)
    else:
        # One batched call for every VERIFIED item's translatable text.
        slots = [
            (i, field)
            for i, f in enumerate(facts)
            if f.status == FactStatus.VERIFIED
            for field in _translatable(f, displays[i])
        ]
        protected = sorted(
            {n for f in facts if f.fact_type == FactType.MEDICATION and (n := _s(f.value or {}, "name"))}
        )
        results: list[str | None] = [None] * len(slots)
        if slots:
            try:
                out = await translation.translate_texts(
                    [getattr(displays[i], field) for i, field in slots], lang, protected_terms=protected
                )
                if len(out) == len(slots):
                    results = list(out)
                else:
                    logger.warning("translate_texts returned %d items for %d inputs", len(out), len(slots))
            except Exception:  # noqa: BLE001 — engine failure must degrade to English, never break the plan
                logger.exception("Care-plan translation failed case_id=%s lang=%s", case_id, lang.value)

        by_item: dict[int, list[tuple[str, str | None]]] = {}
        for (i, field), text in zip(slots, results, strict=True):
            by_item.setdefault(i, []).append((field, text))
        for i, f in enumerate(facts):
            if f.status != FactStatus.VERIFIED:
                statuses.append("pending_review")
                continue
            pairs = by_item.get(i, [])
            if any(text is None for _, text in pairs):
                statuses.append("unavailable")  # keep the whole item in English rather than mix languages
                continue
            displays[i] = displays[i].model_copy(update=dict(pairs))
            statuses.append("translated")

    sections = CarePlanSections()
    for f, d, st in zip(facts, displays, statuses, strict=True):
        item = CarePlanItem(
            **FactWithEvidence.model_validate(f).model_dump(), display=d, translation_status=st
        )
        getattr(sections, SECTION_BY_TYPE[f.fact_type]).append(item)
    for name in _DATE_SORTED:
        getattr(sections, name).sort(key=lambda it: (it.display.date is None, it.display.date or ""))

    audit.record(
        db,
        AuditEvent.CARE_PLAN_GENERATED,
        actor_type=ActorType.PATIENT,
        case_id=case_id,
        language=lang.value,
        item_count=len(facts),
    )
    db.commit()
    return CarePlanResponse(
        case_id=case_id,
        language=lang,
        generated_at=utcnow(),
        counts=case_counts(db, case_id),
        sections=sections,
    )
