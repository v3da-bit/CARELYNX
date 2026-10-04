import asyncio
import uuid
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import SessionLocal
from app.models.entities import Case, Document, Fact, Evidence, ReviewCase, Conflict
from app.models.enums import FactStatus, FactType, ReviewStatus, ReviewSeverity, ReviewReason

def setup_demo():
    db = SessionLocal()
    print("Setting up CARELYNX Hackathon Demo Data...")

    # Create Case
    case_id = uuid.uuid4()
    case = Case(id=case_id)
    db.add(case)
    db.flush()

    # Create Document
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        case_id=case.id,
        filename="discharge_summary_smith.pdf",
        mime_type="application/pdf",
        size_bytes=102400,
        processing_status="COMPLETED"
    )
    db.add(doc)
    db.flush()

    # Create Fact 1: Medication (Verified)
    f1_id = uuid.uuid4()
    f1 = Fact(
        id=f1_id,
        case_id=case.id,
        fact_type=FactType.MEDICATION,
        value={"name": "Lisinopril", "instruction": "Take 10mg daily", "timing": "Morning"},
        status=FactStatus.VERIFIED,
        confidence=0.95,
        extracted_by="amd_vllm_provider"
    )
    db.add(f1)

    # Evidence for f1
    e1 = Evidence(
        fact_id=f1_id,
        document_id=doc.id,
        page_number=1,
        snippet="Patient is to take Lisinopril 10mg daily in the morning.",
        verified=True
    )
    db.add(e1)

    # Create Fact 2: Condition (Verified)
    f2_id = uuid.uuid4()
    f2 = Fact(
        id=f2_id,
        case_id=case.id,
        fact_type=FactType.DOCUMENTED_CONDITION,
        value={"name": "Hypertension"},
        status=FactStatus.VERIFIED,
        confidence=0.99,
        extracted_by="amd_vllm_provider"
    )
    db.add(f2)
    
    # Evidence for f2
    e2 = Evidence(
        fact_id=f2_id,
        document_id=doc.id,
        page_number=1,
        snippet="Primary Diagnosis: Essential Hypertension",
        verified=True
    )
    db.add(e2)

    # Create Fact 3: Encounter Date (Conflict)
    f3_id = uuid.uuid4()
    f3 = Fact(
        id=f3_id,
        case_id=case.id,
        fact_type=FactType.ENCOUNTER_DATE,
        value={"date": "2026-10-14", "kind": "follow_up"},
        status=FactStatus.CONFLICT_DETECTED,
        confidence=0.88,
        extracted_by="amd_vllm_provider"
    )
    db.add(f3)

    e3 = Evidence(
        fact_id=f3_id,
        document_id=doc.id,
        page_number=2,
        snippet="Follow up on Oct 14",
        verified=True
    )
    db.add(e3)

    f4_id = uuid.uuid4()
    f4 = Fact(
        id=f4_id,
        case_id=case.id,
        fact_type=FactType.ENCOUNTER_DATE,
        value={"date": "2026-10-16", "kind": "follow_up"},
        status=FactStatus.CONFLICT_DETECTED,
        confidence=0.89,
        extracted_by="amd_vllm_provider"
    )
    db.add(f4)

    e4 = Evidence(
        fact_id=f4_id,
        document_id=doc.id,
        page_number=3,
        snippet="Cardiology follow up scheduled for 10/16",
        verified=True
    )
    db.add(e4)

    db.flush()

    # Create Conflict
    conflict_id = uuid.uuid4()
    conflict = Conflict(
        id=conflict_id,
        case_id=case.id,
        fact_type=FactType.ENCOUNTER_DATE,
        conflict_data={
            "context": "encounter_date_follow_up", 
            "fact_ids": [str(f3_id), str(f4_id)]
        }
    )
    db.add(conflict)
    db.flush()

    # Create Review Case
    review = ReviewCase(
        id=uuid.uuid4(),
        case_id=case.id,
        reason="Conflicting encounter_date extracted",
        reason_code=ReviewReason.CONFLICT,
        severity=ReviewSeverity.HIGH,
        fact_ids=[str(f3_id), str(f4_id)],
        conflict_id=conflict_id,
        status=ReviewStatus.OPEN
    )
    db.add(review)

    db.commit()
    print(f"Demo Data Setup Complete!\nDemo Case ID: {case.id}")

if __name__ == "__main__":
    setup_demo()
