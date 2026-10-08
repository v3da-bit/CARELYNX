import uuid
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Fact, Conflict, ReviewCase, Case
from app.models.enums import FactStatus, FactType, ConflictStatus, ReviewSeverity, ReviewStatus, ReviewReason, ActorType, AuditEvent
from app.services import audit

logger = logging.getLogger(__name__)

import uuid
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Fact, Conflict, ReviewCase, Case
from app.models.enums import FactStatus, FactType, ConflictStatus, ReviewSeverity, ReviewStatus, ReviewReason, ActorType, AuditEvent
from app.services import audit

logger = logging.getLogger(__name__)

def detect_conflicts(db: Session, case_id: uuid.UUID) -> None:
    """Detect real clinical conflicts across facts in a case and create review cases."""
    facts = db.scalars(select(Fact).where(Fact.case_id == case_id)).all()
    
    # Group facts by meaningful clinical entity keys
    # e.g., Medication name (Lisinopril vs Lisinopril), Encounter kind (admission vs discharge)
    conflict_buckets: dict[tuple[FactType, str], list[Fact]] = {}
    
    for fact in facts:
        # Ignore rejected facts
        if fact.status == FactStatus.REJECTED:
            continue
            
        if fact.fact_type == FactType.MEDICATION:
            med_name = (fact.value.get("name") or "unspecified").lower().strip()
            # Normalize common names (e.g. remove strength if in name)
            import re
            base_name = re.sub(r"\d+\s*(?:mg|mcg|g|ml)", "", med_name).strip()
            conflict_buckets.setdefault((FactType.MEDICATION, base_name), []).append(fact)
            
        elif fact.fact_type == FactType.ENCOUNTER_DATE:
            kind = (fact.value.get("kind") or "encounter").lower().strip()
            conflict_buckets.setdefault((FactType.ENCOUNTER_DATE, kind), []).append(fact)
            
        elif fact.fact_type == FactType.FOLLOW_UP:
            # Check appointment specialty or raw text target
            raw = (fact.value.get("raw_text") or "").lower()
            specialty = "pcp" if "primary" in raw or "pcp" in raw else "pulmonology" if "pulmon" in raw else "cardiology" if "cardio" in raw else "specialist"
            conflict_buckets.setdefault((FactType.FOLLOW_UP, specialty), []).append(fact)
            
        elif fact.fact_type == FactType.DOCUMENTED_CONDITION:
            # Having multiple diagnoses (e.g. Pneumonia + Hypertension) is normal comorbidity, not a conflict
            pass
            
        elif fact.fact_type == FactType.INSTRUCTION:
            # Having multiple distinct instructions is normal care
            pass

    for (fact_type, entity_key), group in conflict_buckets.items():
        if len(group) <= 1:
            continue
        _check_fact_group_for_conflicts(db, case_id, fact_type, group, f"{fact_type.value}: {entity_key}")

def _check_fact_group_for_conflicts(db: Session, case_id: uuid.UUID, fact_type: FactType, group: list[Fact], context: str) -> None:
    if len(group) <= 1:
        return
        
    import json
    unique_values: dict[str, list[Fact]] = {}
    for f in group:
        if f.status == FactStatus.REJECTED:
            continue
        # Compare normalized values (e.g. strength, frequency, date)
        val_str = json.dumps(f.value, sort_keys=True)
        unique_values.setdefault(val_str, []).append(f)
        
    if len(unique_values) > 1:
        # Check if an open conflict already exists for these facts
        existing_conflict = db.scalars(
            select(Conflict).where(
                Conflict.case_id == case_id, 
                Conflict.fact_type == fact_type,
                Conflict.status == ConflictStatus.OPEN
            )
        ).first()
        
        if existing_conflict:
            return # Already tracking this conflict
            
        logger.warning(f"Clinical conflict detected for case {case_id}, context '{context}'")
        
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
            f.status = FactStatus.CONFLICT_DETECTED
            existing_reasons = f.status_reasons or []
            if "Conflicting values detected across documents" not in existing_reasons:
                f.status_reasons = existing_reasons + ["Conflicting values detected across documents"]
        
        # Create a ReviewCase
        review = ReviewCase(
            case_id=case_id,
            reason=f"Clinical conflict detected: {context}",
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

