import asyncio
import time
import uuid
import os
import sys

# Setup import path for apps.api
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.entities import Case, Document, Fact
from app.models.enums import ProcessingStatus
from app.core.config import get_settings
from app.services.documents import create_case, upload_document
from app.services.ocr import get_ocr_engine
from app.services.pipeline import run_document
from app.storage.local import get_storage

# pyrefly: ignore [unannotated-return]
async def run_evaluation():
    db = SessionLocal()
    storage = get_storage()
    print("CARELYNX Evaluation Benchmark")
    print("============================")
    
    # We will just evaluate whatever is in tests/data/ if it exists, or create a mock pass.
    sample_dir = os.path.join(os.path.dirname(__file__), '..', 'tests', 'data')
    
    files_to_test = []
    if os.path.exists(sample_dir):
        files_to_test = [os.path.join(sample_dir, f) for f in os.listdir(sample_dir) if f.endswith('.pdf') or f.endswith('.jpg')]
    
    if not files_to_test:
        print("No sample files found in tests/data/. Creating a dummy pass.")
        return
        
    print(f"Found {len(files_to_test)} files to evaluate.")
    
    total_facts = 0
    total_time = 0.0
    
    for file_path in files_to_test:
        print(f"\nProcessing {os.path.basename(file_path)}...")
        
        # Setup case
        case = create_case(db)
        db.commit()
        
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            
        doc = upload_document(
            db, storage, data=file_bytes, filename=os.path.basename(file_path),
            max_bytes=get_settings().max_upload_bytes, case_id=case.id,
        )
        db.commit()
        
        start_time = time.time()
        
        # run_document is what POST /documents/{id}/process runs; called directly here
        try:
            await run_document(db, storage, doc, ocr=get_ocr_engine())
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
            
        end_time = time.time()
        duration = end_time - start_time
        total_time += duration
        
        # Get facts
        facts = db.scalars(select(Fact).where(Fact.case_id == case.id)).all()
        fact_count = len(facts)
        total_facts += fact_count
        
        print(f"  -> Extracted {fact_count} facts in {duration:.2f} seconds.")
        
    print("\n============================")
    print("EVALUATION COMPLETE")
    print(f"Total files: {len(files_to_test)}")
    print(f"Total facts extracted: {total_facts}")
    print(f"Average time per file: {total_time / len(files_to_test):.2f}s")
    
if __name__ == "__main__":
    asyncio.run(run_evaluation())
