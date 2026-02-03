import os
from backend.database import SessionLocal
from backend.models import Document
from backend.storage import storage
from sqlalchemy.orm import Session
import sys

# Ensure backend package is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

def migrate_to_cloud():
    db: Session = SessionLocal()
    
    # 1. Find all local files
    docs = db.query(Document).filter(Document.path.notilike("s3://%")).all() # Exclude already migrated? Or just "http"
    # Better: Filter for paths that exist on disk
    
    print(f"Found {len(docs)} documents to check for migration...")
    
    count = 0
    for doc in docs:
        if "jmail" in doc.path or "http" in doc.path:
            continue
            
        # Resolve local path (using logic from main.py approximately)
        local_path = doc.path
        if not os.path.isabs(local_path):
             # Try relative to cwd or backend?
             # Based on previous debugging, paths are like 'data/files/...' relative to root
             candidates = [
                 local_path,
                 os.path.join("data", "files", os.path.basename(local_path)),
                 os.path.join("data", "files", doc.filename)
             ]
             
             real_path = None
             for c in candidates:
                 if os.path.exists(c):
                     real_path = c
                     break
             
             if not real_path:
                 print(f" [SKIP] Local file not found for: {doc.filename} (Path: {doc.path})")
                 continue
                 
             # Found it! Upload.
             print(f" [MIGRATING] Uploading {doc.filename}...")
             
             # Use filename as object key to keep it flat or structure it? Flat for now.
             object_key = f"documents/{doc.filename}"
             
             try:
                 # Check if we have credentials? Assume yes or error will verify.
                 s3_url = storage.upload_file(real_path, object_key)
                 if s3_url:
                     doc.path = s3_url
                     db.commit() # Commit immediately so it's live
                     count += 1
                     print(f"   -> Success! New path: {s3_url}")
             except Exception as e:
                 print(f"   -> FAILED: {e}")

    print(f"\nMigration complete. {count} documents migrated to S3.")

if __name__ == "__main__":
    if not os.getenv("AWS_ACCESS_KEY_ID"):
        print("WARNING: AWS Credentials not found in env. Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set.")
        # Proceed anyway, maybe using ~/.aws/credentials
    
    migrate_to_cloud()
