import os
from backend.models import Document
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Mock Backend Logic
def resolve_path(doc_path):
    # current_dir should be .../backend relative to where this script runs? 
    # Actually this script is in root. backend/main.py is in backend/
    
    # Simulate backend/main.py location
    backend_dir = os.path.abspath("backend")
    project_root = os.path.dirname(backend_dir)
    
    print(f"Mock Backend Dir: {backend_dir}")
    print(f"Mock Project Root: {project_root}")
    print(f"Input Doc Path: {doc_path}")

    possible_paths = []
    possible_paths.append(doc_path)
    possible_paths.append(os.path.join(project_root, doc_path))
    possible_paths.append(os.path.join(backend_dir, doc_path))
    
    if "/" not in doc_path and "\\" not in doc_path:
        possible_paths.append(os.path.join(project_root, "data", "files", doc_path))

    for p in possible_paths:
        p = p.replace("/", os.sep).replace("\\", os.sep)
        print(f" - Checking: {p}")
        if os.path.exists(p) and os.path.isfile(p):
            print(f"   -> FOUND! Size: {os.path.getsize(p)} bytes")
            return p
            
    print("   -> NOT FOUND in any candidate path.")
    return None

def verify_doc_7():
    print("Connecting to DB...")
    engine = create_engine("sqlite:///./backend/vault_epstein.db")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    doc = db.get(Document, 7)
    if not doc:
        print("Doc 7 missing in DB")
        return

    print(f"Doc 7 Path in DB: {doc.path}")
    resolved = resolve_path(doc.path)
    
    if resolved:
        print("\nSUCCESS: File exists and logical resolution works.")
    else:
        print("\nFAILURE: File not found.")

if __name__ == "__main__":
    verify_doc_7()
