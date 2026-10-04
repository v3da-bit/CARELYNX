import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import Fact, Evidence
from app.schemas.fact import FactResponse, EvidenceResponse

router = APIRouter(prefix="/facts", tags=["Facts"])

@router.get("/{fact_id}", response_model=FactResponse)
def get_fact(fact_id: uuid.UUID, db: Session = Depends(get_db)) -> Any:
    fact = db.get(Fact, fact_id)
    if not fact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fact not found")
    return fact

@router.get("/{fact_id}/evidence", response_model=list[EvidenceResponse])
def get_fact_evidence(fact_id: uuid.UUID, db: Session = Depends(get_db)) -> Any:
    fact = db.get(Fact, fact_id)
    if not fact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fact not found")
    
    evidence_records = db.scalars(
        select(Evidence).where(Evidence.fact_id == fact_id)
    ).all()
    
    return evidence_records
