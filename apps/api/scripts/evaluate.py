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
from app.services.processing import process_document
from app.services.documents import create_case, create_document

async def run_evaluation():
    db = SessionLocal()
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
            
        doc = create_document(db, case.id, os.path.basename(file_path), "application/pdf", len(file_bytes))
        db.commit()
        
        # Save mock file (in a real scenario we use proper storage, here we just pass bytes or write to temp)
        # Assuming process_document takes doc and db
        start_time = time.time()
        
        # Mocking process_document call structure
        # process_document runs in background normally, but we run it directly here
        try:
            await process_document(db, doc, file_bytes)
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
