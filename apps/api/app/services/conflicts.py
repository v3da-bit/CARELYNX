import uuid
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Fact, Conflict, ReviewCase, Case
from app.models.enums import FactStatus, FactType, ConflictStatus, ReviewSeverity, ReviewStatus, ReviewReason, ActorType, AuditEvent
from app.services import audit

logger = logging.getLogger(__name__)

def detect_conflicts(db: Session, case_id: uuid.UUID) -> None:
    """Detect conflicts between facts in a case and create review cases."""
    facts = db.scalars(select(Fact).where(Fact.case_id == case_id)).all()
    
    # Group facts by type
    facts_by_type: dict[FactType, list[Fact]] = {}
    for fact in facts:
        facts_by_type.setdefault(fact.fact_type, []).append(fact)
    
    for fact_type, grouped_facts in facts_by_type.items():
        if len(grouped_facts) <= 1:
            continue
            
        # For encounter dates, we only conflict if they are of the same kind (admission vs discharge)
        if fact_type == FactType.ENCOUNTER_DATE:
            dates_by_kind = {}
            for f in grouped_facts:
                kind = f.value.get("kind")
                date_val = f.value.get("date")
                if kind and date_val:
                    dates_by_kind.setdefault(kind, []).append(f)
            
            for kind, kind_facts in dates_by_kind.items():
                _check_fact_group_for_conflicts(db, case_id, fact_type, kind_facts, f"encounter_date_{kind}")
        else:
            _check_fact_group_for_conflicts(db, case_id, fact_type, grouped_facts, fact_type.value)

def _check_fact_group_for_conflicts(db: Session, case_id: uuid.UUID, fact_type: FactType, group: list[Fact], context: str) -> None:
    if len(group) <= 1:
        return
        
    # Simplify: check if values are distinct (using json string representation for comparison)
    import json
    unique_values = {}
    for f in group:
        # Ignore rejected facts
        if f.status == FactStatus.REJECTED:
            continue
            
        val_str = json.dumps(f.value, sort_keys=True)
        unique_values.setdefault(val_str, []).append(f)
        
    if len(unique_values) > 1:
        # We have a conflict!
        # Check if a conflict already exists for these facts
        # For MVP, we'll just create a new conflict if one doesn't exist for this fact_type
        existing_conflict = db.scalars(
            select(Conflict).where(
                Conflict.case_id == case_id, 
                Conflict.fact_type == fact_type,
                Conflict.status == ConflictStatus.OPEN
            )
        ).first()
        
        if existing_conflict:
            return # Already tracking this conflict
            
        logger.warning(f"Conflict detected for case {case_id}, fact_type {fact_type}")
        
        conflict_data = {
            "context": context,
            "values": list(unique_values.keys()),
            "fact_ids": [str(f.id) for f in group]
        }
        
        conflict = Conflict(
            case_id=case_id,
            fact_type=fact_type,
            conflict_data=conflict_data,
            status=ConflictStatus.OPEN
        )
        db.add(conflict)
        db.flush()
        
        # Mark all involved facts as CONFLICT_DETECTED
        for f in group:
            if f.status != FactStatus.VERIFIED and f.status != FactStatus.HUMAN_REQUIRED:
                continue
            f.status = FactStatus.CONFLICT_DETECTED
            f.status_reasons = f.status_reasons + ["Conflicting values detected across documents"]
        
        # Create a ReviewCase
        review = ReviewCase(
            case_id=case_id,
            reason=f"Conflict detected for {context}",
            reason_code=ReviewReason.CONFLICT,
            severity=ReviewSeverity.HIGH,
            conflict_id=conflict.id,
            fact_ids=[str(f.id) for f in group],
            status=ReviewStatus.OPEN
        )
        db.add(review)
        
        audit.record(
            db,
            AuditEvent.CONFLICT_CREATED,
            actor_type=ActorType.SYSTEM,
            case_id=case_id,
            conflict_id=str(conflict.id)
        )
        
        audit.record(
            db,
            AuditEvent.REVIEW_CREATED,
            actor_type=ActorType.SYSTEM,
            case_id=case_id,
            review_id=str(review.id)
        )
