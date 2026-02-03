from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Document, Page, Entity, FlightLog

# Connect to the database
SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/vault_epstein.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("--- DOCUMENTS ---")
docs = db.query(Document).all()
for d in docs:
    print(f"ID: {d.id}, Filename: {d.filename}, Path: {d.path}")

print("\n--- PAGES (First 5) ---")
pages = db.query(Page).limit(5).all()
for p in pages:
    print(f"DocID: {p.document_id}, PageNum: {p.page_num}, CSS Content: {p.text_content[:50]}...")

print("\n--- DOC ID 7 CHECK (DATASET_3) ---")
d7 = db.get(Document, 7)
if d7:
    print(f"ID: {d7.id}, Filename: {d7.filename}, Path: {d7.path}")
else:
    print("Doc ID 7 not found.")
    
print("\n--- JMAIL DOC CHECK ---")
docs = db.query(Document).filter(Document.filename.ilike("%JMAIL%")).all()
for d in docs:
    print(f"ID: {d.id}, Filename: {d.filename}, Path: {d.path}, ExtURL: {d.external_url}")
    
print("\n--- FLIGHT LOGS CHECK ---")
count = db.query(FlightLog).count()
print(f"Total Flight Logs: {count}")
if count > 0:
    first = db.query(FlightLog).first()
    print(f"Sample: {first.date} | {first.tail_number} | {first.origin}->{first.destination}")

db.close()
