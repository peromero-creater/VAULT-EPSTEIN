from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Document
import os

# Connect to DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/vault_epstein.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def fix_paths():
    print("Fixing paths for PDF documents...")
    # Find all PDFs
    docs = db.query(Document).filter(Document.doc_type == "PDF").all()
    
    for d in docs:
        if d.external_url:
            continue
            
        print(f"Checking {d.filename} (Current Path: {d.path})")
        
        # Check if current path exists relative to CWD
        if os.path.exists(d.path):
            print(" - Path exists.")
            continue
            
        # Try finding it in data/files
        potential = os.path.join("data", "files", d.filename)
        if os.path.exists(potential):
            print(f" - Found in data/files! Updating path to: {potential}")
            d.path = potential
        else:
            print(f" - Not found in data/files either.")

    db.commit()
    print("Path correction complete.")

if __name__ == "__main__":
    fix_paths()
