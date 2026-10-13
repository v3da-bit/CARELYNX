"""Fact + evidence endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.db.session import get_db
from app.models import Evidence, Fact
from app.schemas.fact import EvidenceResponse, FactResponse

router = APIRouter(prefix="/facts", tags=["facts"])


def _get_fact(db: Session, fact_id: uuid.UUID) -> Fact:
    fact = db.get(Fact, fact_id)
    if fact is None:
        raise AppError(ErrorCode.NOT_FOUND, "Fact not found.", 404)
    return fact


@router.get("/{fact_id}", response_model=FactResponse)
def get_fact(fact_id: uuid.UUID, db: Session = Depends(get_db)) -> Fact:
    return _get_fact(db, fact_id)


@router.get("/{fact_id}/evidence", response_model=list[EvidenceResponse])
def get_fact_evidence(fact_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Evidence]:
    return sorted(
        _get_fact(db, fact_id).evidence, key=lambda e: (e.page_number, e.char_start or 0, str(e.id))
    )
