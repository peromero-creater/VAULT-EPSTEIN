import os
import fitz  # PyMuPDF
import sys
from pathlib import Path
from sqlalchemy.orm import Session
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import SessionLocal, init_db
from models import Document, Page, Entity, PageEntity, CountryStats, PersonCountryCoMention
from processor import mask_pii, extract_entities, get_text_quality
from normalization import normalize_country

DATA_DIR = Path("/data/files")
ZIPS_DIR = Path("/data/zips")

def process_pdf(file_path: Path, db: Session):
    print(f"Processing PDF: {file_path.name}")
    doc = Document(
        filename=file_path.name,
        path=str(file_path),
        doc_type="PDF"
    )
    db.add(doc)
    db.flush() # Get doc.id
    
    pdf_doc = fitz.open(file_path)
    for page_num in range(len(pdf_doc)):
        page = pdf_doc.load_page(page_num)
        text = page.get_text()
        
        # Mask PII for storage and search
        masked_text = mask_pii(text)
        quality = get_text_quality(text)
        
        db_page = Page(
            document_id=doc.id,
            page_num=page_num + 1,
            text_content=masked_text,
            text_quality=quality,
            media_type="page_image"
        )
        db.add(db_page)
        db.flush()
        
        # Extract and save entities
        entities = extract_entities(text)
        process_entities(db, db_page, entities)
        
    db.commit()

def process_entities(db: Session, page: Page, entities_dict: dict):
    for ent_type, names in entities_dict.items():
        for name in names:
            # Upsert Entity
            db_entity = db.query(Entity).filter_by(name=name, type=ent_type).first()
            if not db_entity:
                db_entity = Entity(name=name, type=ent_type)
                if ent_type in ["GPE", "LOC"]:
                    db_entity.country_code = normalize_country(name)
                db.add(db_entity)
                db.flush()
            
            # Save link
            pe = PageEntity(page_id=page.id, entity_id=db_entity.id)
            db.add(pe)
            
            # Update Country/Co-mention stats
            if db_entity.country_code:
                update_country_stats(db, db_entity.country_code)
                # Link person entities in the same page to this country
                # (This is handled in a separate aggregation step usually, 
                # but we can do simple increments here)

def update_country_stats(db: Session, country_code: str):
    stats = db.query(CountryStats).filter_by(country_code=country_code).first()
    if not stats:
        stats = CountryStats(country_code=country_code, doc_count=1, page_count=1)
        db.add(stats)
    else:
        stats.page_count += 1
        # doc_count logic would need tracking docs per country

def main():
    init_db()
    db = SessionLocal()
    
    # Simple scan
    if not DATA_DIR.exists():
        print(f"Data directory {DATA_DIR} not found.")
        return

    for file_path in DATA_DIR.glob("*.pdf"):
        # Check if already processed
        exists = db.query(Document).filter_by(filename=file_path.name).first()
        if not exists:
            process_pdf(file_path, db)
            
    db.close()

if __name__ == "__main__":
    main()
