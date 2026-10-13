"""Deterministic cross-document conflict detection (SAFETY.md §3). Never picks a winner.

Facts are grouped by (fact_type, subject):
  medication     → normalised drug name          compared on strength, frequency
  follow_up      → normalised department bucket  compared on date, time
  encounter_date → admission / discharge         compared on date
  allergy        → one bucket                    compared on "no known allergies" vs a listed allergy
Values are normalised (case, whitespace, "40mg" == "40 mg") so wording noise is not a conflict, and a field is
only compared when both facts state it.

Status choice: a conflict raises VERIFIED/NEEDS_REVIEW facts to CONFLICT_DETECTED, but never overwrites the
stricter HUMAN_REQUIRED (the item already must not be shown as actionable and has its own review); such facts
get
the conflict reason appended and are still linked in the conflict review. REJECTED facts are ignored.
"""

from __future__ import annotations

import logging
import re
import uuid
from itertools import combinations
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Conflict, Fact, ReviewCase
from app.models.enums import (
    ActorType,
    AuditEvent,
    ConflictStatus,
    FactStatus,
    FactType,
    ReviewReason,
    ReviewSeverity,
    ReviewStatus,
)
from app.services import audit

logger = logging.getLogger(__name__)

CONFLICT_REASON = "Conflicting values detected across documents"
COMPARED_FIELDS: dict[FactType, tuple[str, ...]] = {
    FactType.MEDICATION: ("strength", "frequency"),
    FactType.FOLLOW_UP: ("date", "time"),
    FactType.ENCOUNTER_DATE: ("date",),
    FactType.ALLERGY: ("no_known_allergies",),
}
_DEPT_NOISE = {"opd", "clinic", "department", "dept", "the", "outpatient", "op"}
_RECOMMENDED = {
    FactType.FOLLOW_UP: "Confirm the correct follow-up date and time with the treating clinic.",
    FactType.MEDICATION: "Confirm the correct medication instruction with the prescribing clinician.",
}


def normalize(v: Any) -> Any:
    if not isinstance(v, str):
        return v
    s = re.sub(r"\s+", " ", v.strip().lower())
    return re.sub(r"(\d)\s*(mg|mcg|g|ml|iu|units?|%)\b", r"\1 \2", s)


def subject_of(fact: Fact) -> str | None:
    v = fact.value or {}
    if fact.fact_type == FactType.MEDICATION:
        return re.sub(r"[^a-z0-9]", "", str(v.get("name") or "").lower()) or None
    if fact.fact_type == FactType.FOLLOW_UP:
        words = re.findall(r"[a-z]+", str(v.get("department") or "").lower())
        return " ".join(w for w in words if w not in _DEPT_NOISE) or "unspecified"
    if fact.fact_type == FactType.ENCOUNTER_DATE:
        return str(v.get("kind") or "") or None
    if fact.fact_type == FactType.ALLERGY:
        return "allergies"
    return None  # several instructions/conditions/warning signs are normal, never a conflict


def values_conflict(fact_type: FactType, a: dict[str, Any], b: dict[str, Any]) -> bool:
    for f in COMPARED_FIELDS[fact_type]:
        va, vb = normalize(a.get(f)), normalize(b.get(f))
        if va is not None and vb is not None and va != vb:
            return True
    return False


def detect_conflicts(db: Session, case_id: uuid.UUID) -> None:
    """Detect conflicts across all non-rejected facts of a case and open HIGH-severity reviews."""
    groups: dict[tuple[FactType, str], list[Fact]] = {}
    for fact in db.scalars(select(Fact).where(Fact.case_id == case_id).order_by(Fact.created_at, Fact.id)):
        if fact.status == FactStatus.REJECTED:
            continue
        subject = subject_of(fact)
        if subject is not None:
            groups.setdefault((fact.fact_type, subject), []).append(fact)

    for (fact_type, subject), group in groups.items():
        involved = {
            f.id: f
            for a, b in combinations(group, 2)
            if values_conflict(fact_type, a.value, b.value)
            for f in (a, b)
        }
        if involved:
            _record_conflict(db, case_id, fact_type, subject, list(involved.values()))


def _record_conflict(
    db: Session, case_id: uuid.UUID, fact_type: FactType, subject: str, facts: list[Fact]
) -> None:
    for f in facts:
        if f.status in (FactStatus.VERIFIED, FactStatus.NEEDS_REVIEW):
            f.status = FactStatus.CONFLICT_DETECTED
        if CONFLICT_REASON not in (f.status_reasons or []):
            f.status_reasons = [*(f.status_reasons or []), CONFLICT_REASON]
    fact_ids = [str(f.id) for f in facts]

    existing = next(
        (
            c
            for c in db.scalars(
                select(Conflict).where(
                    Conflict.case_id == case_id,
                    Conflict.fact_type == fact_type,
                    Conflict.status == ConflictStatus.OPEN,
                )
            )
            if (c.conflict_data or {}).get("subject") == subject
        ),
        None,
    )
    if existing is not None:  # a later document joined an open conflict: link its facts, don't duplicate
        merged = list(dict.fromkeys([*existing.conflict_data.get("fact_ids", []), *fact_ids]))
        existing.conflict_data = {**existing.conflict_data, "fact_ids": merged}
        review = db.scalars(select(ReviewCase).where(ReviewCase.conflict_id == existing.id)).first()
        if review is not None and review.status == ReviewStatus.OPEN:
            review.fact_ids = list(dict.fromkeys([*(review.fact_ids or []), *fact_ids]))
        return

    logger.warning("Conflict detected case_id=%s fact_type=%s facts=%d", case_id, fact_type.value, len(facts))
    conflict = Conflict(
        case_id=case_id,
        fact_type=fact_type,
        conflict_data={"subject": subject, "fields": list(COMPARED_FIELDS[fact_type]), "fact_ids": fact_ids},
        status=ConflictStatus.OPEN,
    )
    db.add(conflict)
    db.flush()
    review = ReviewCase(
        case_id=case_id,
        reason=f"Conflicting {fact_type.value} values across documents ({subject})",
        reason_code=ReviewReason.CONFLICT,
        severity=ReviewSeverity.HIGH,
        conflict_id=conflict.id,
        fact_ids=fact_ids,
        status=ReviewStatus.OPEN,
        recommended_action=_RECOMMENDED.get(fact_type, "Confirm the correct value with the treating clinic."),
    )
    db.add(review)
    db.flush()
    audit.record(
        db,
        AuditEvent.CONFLICT_CREATED,
        actor_type=ActorType.SYSTEM,
        case_id=case_id,
        conflict_id=str(conflict.id),
        fact_type=fact_type.value,
    )
    audit.record(
        db,
        AuditEvent.REVIEW_CREATED,
        actor_type=ActorType.SYSTEM,
        case_id=case_id,
        review_id=str(review.id),
        review_reason=ReviewReason.CONFLICT.value,
    )
