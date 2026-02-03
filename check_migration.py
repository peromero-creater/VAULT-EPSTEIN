import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Document
from backend.storage import storage
from dotenv import load_dotenv

load_dotenv()

db_url = "sqlite:///./backend/vault_epstein.db"
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def check_migrated(doc_id):
    doc = db.get(Document, doc_id)
    if not doc:
        print(f"Doc {doc_id} NOT FOUND")
        return
    
    print(f"Doc {doc_id} ({doc.filename}):")
    print(f" - Path: {doc.path}")
    
    if doc.path.startswith("s3://"):
        print(f" - MIGRATED: YES")
        # Generate URL
        url = storage.get_presigned_url(doc.path)
        print(f" - Presigned URL: {url}")
    else:
        print(f" - MIGRATED: NO")

# Check known docs
print("--- Checking Migration Status ---")

# 1332-16 (We know this is uploaded)
# First we need to find its ID if we don't know it.
doc_1 = db.query(Document).filter(Document.filename.like("%1332-16%")).first()
if doc_1:
    check_migrated(doc_1.id)
else:
    print("Could not find 1332-16 in DB")

# DataSet_1 (Uploaded)
doc_2 = db.query(Document).filter(Document.filename.like("%DataSet_1_COMPLETE%")).first()
if doc_2:
    check_migrated(doc_2.id)

# DataSet_2 (Uploading...)
doc_3 = db.query(Document).filter(Document.filename.like("%DataSet_2_COMPLETE%")).first()
if doc_3:
    check_migrated(doc_3.id)
    
# DataSet_3 (ID 7)
check_migrated(7)
