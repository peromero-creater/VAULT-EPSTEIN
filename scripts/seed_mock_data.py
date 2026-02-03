import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import SessionLocal, init_db
from models import Document, Page

def seed():
    init_db()
    db = SessionLocal()
    
    # Check if data already exists
    if db.query(Document).first():
        print("Database already seeded.")
        db.close()
        return

    print("Seeding mock data...")
    doc = Document(filename="Epstein_Flight_Logs.pdf", path="mock/path", doc_type="PDF")
    db.add(doc)
    db.flush()

    pages = [
        "Jeffrey Epstein and Ghislaine Maxwell were spotted at the charity gala.",
        "Flight logs from 2002 indicate several trips to Little St. James island.",
        "Trump was seen at a social event in Mar-a-Lago in 1997.",
        "Bill Clinton's name appears in the flight logs multiple times in 2003.",
        "Zorro Ranch investigation records detail the property layout in New Mexico."
    ]

    for i, content in enumerate(pages):
        page = Page(document_id=doc.id, page_num=i+1, text_content=content, media_type="page_image")
        db.add(page)

    db.commit()
    db.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed()
