"""
Production Data Seeding Script
Runs on deployment to populate database with initial Epstein document data
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from database import SessionLocal, init_db
from models import Document, Page, Entity, Relationship
from datetime import datetime

def seed_database():
    """Seed database with initial data for production deployment"""
    
    print("\n" + "="*60)
    print("PRODUCTION DATABASE SEEDING")
    print("="*60 + "\n")
    
    init_db()
    db = SessionLocal()
    
    try:
        # Check if already seeded
        existing_docs = db.query(Document).count()
        if existing_docs > 0:
            print(f"✓ Database already seeded ({existing_docs} documents exist)")
            print("  To reseed, delete the database file and run again\n")
            return
        
        print("Seeding database with initial Epstein investigation data...\n")
        
        # Seed key entities
        entities_data = [
            {"name": "Jeffrey Epstein", "type": "PERSON"},
            {"name": "Ghislaine Maxwell", "type": "PERSON"},
            {"name": "Bill Clinton", "type": "PERSON"},
            {"name": "Prince Andrew", "type": "PERSON"},
            {"name": "Donald Trump", "type": "PERSON"},
            {"name": "Alan Dershowitz", "type": "PERSON"},
            {"name": "Little St. James", "type": "LOCATION", "country_code": "VI"},
            {"name": "Palm Beach", "type": "LOCATION", "country_code": "US"},
            {"name": "New York", "type": "LOCATION", "country_code": "US"},
            {"name": "London", "type": "LOCATION", "country_code": "GB"},
            {"name": "Paris", "type": "LOCATION", "country_code": "FR"},
            {"name": "US Virgin Islands", "type": "LOCATION", "country_code": "VI"},
            {"name": "Manhattan", "type": "LOCATION", "country_code": "US"},
            {"name": "Zorro Ranch", "type": "LOCATION", "country_code": "US"},
            {"name": "Dubai", "type": "LOCATION", "country_code": "AE"},
            {"name": "Singapore", "type": "LOCATION", "country_code": "SG"},
            {"name": "South Africa", "type": "LOCATION", "country_code": "ZA"},
            {"name": "San Francisco", "type": "LOCATION", "country_code": "US"},
        ]
        
        entity_map = {}
        for ent_data in entities_data:
            entity = Entity(
                name=ent_data["name"],
                type=ent_data["type"],
                normalized_name=ent_data["name"].upper(),
                country_code=ent_data.get("country_code")
            )
            db.add(entity)
            db.flush()
            entity_map[ent_data["name"]] = entity
            print(f"  ✓ Entity: {ent_data['name']} ({ent_data['type']})")
        
        print(f"\n✅ Created {len(entity_map)} entities\n")
        
        # Seed relationships
        relationships_data = [
            {
                "source": "Jeffrey Epstein",
                "target": "Ghislaine Maxwell",
                "type": "CO_CONSPIRATOR",
                "description": "Coordinated recruitment and travel. Maxwell acted as Epstein's associate in alleged trafficking operations."
            },
            {
                "source": "Jeffrey Epstein",
                "target": "Bill Clinton",
                "type": "FLIGHT_PASSENGER",
                "description": "Multiple documented flights on Epstein's private aircraft to various international destinations."
            },
            {
                "source": "Jeffrey Epstein",
                "target": "Prince Andrew",
                "type": "ASSOCIATE",
                "description": "Social connections documented through photographs and witness testimony at multiple properties."
            },
            {
                "source": "Jeffrey Epstein",
                "target": "Donald Trump",
                "type": "SOCIAL_ACQUAINTANCE",
                "description": "Historical social connections in Palm Beach and New York social circles in the 1990s-2000s."
            },
            {
                "source": "Jeffrey Epstein",
                "target": "Alan Dershowitz",
                "type": "LEGAL_REPRESENTATION",
                "description": "Legal representation during 2008 plea deal negotiations."
            },
            {
                "source": "Ghislaine Maxwell",
                "target": "Prince Andrew",
                "type": "ASSOCIATE",
                "description": "Long-standing social connections documented in multiple jurisdictions."
            },
            {
                "source": "Jeffrey Epstein",
                "target": "Little St. James",
                "type": "PROPERTY_OWNER",
                "description": "Primary private island property in U.S. Virgin Islands, site of alleged criminal activity."
            },
        ]
        
        for rel_data in relationships_data:
            relationship = Relationship(
                source_entity_id=entity_map[rel_data["source"]].id,
                target_entity_id=entity_map[rel_data["target"]].id,
                rel_type=rel_data["type"],
                description=rel_data["description"],
                confidence_score=0.9
            )
            db.add(relationship)
            print(f"  ✓ {rel_data['source']} → {rel_data['target']} ({rel_data['type']})")
        
        print(f"\n✅ Created {len(relationships_data)} relationships\n")
        
        # Seed sample documents with metadata
        documents_data = [
            {
                "filename": "Flight_Logs_Compilation.pdf",
                "description": "Comprehensive compilation of Epstein's private aircraft flight logs spanning 1997-2005, documenting passenger manifests and international travel routes.",
                "dataset": "Public-Records"
            },
            {
                "filename": "Maxwell_Trial_Transcript_Day1.pdf",
                "description": "Federal court transcript from Ghislaine Maxwell trial, day 1. Includes opening statements and initial witness testimony.",
                "dataset": "Court-Documents"
            },
            {
                "filename": "Epstein_Black_Book.pdf",
                "description": "Contact directory containing hundreds of names, addresses, and phone numbers from Epstein's personal records, released in 2015.",
                "dataset": "Public-Records"
            },
        ]
        
        for doc_data in documents_data:
            document = Document(
                filename=doc_data["filename"],
                path=f"/vault/seeded/{doc_data['filename']}",
                external_url=f"https://vault-epstein.com/docs/{doc_data['filename'].replace(' ', '_')}",
                doc_type="PDF",
                dataset=doc_data["dataset"],
                added_at=datetime.utcnow()
            )
            db.add(document)
            db.flush()
            
            # Add sample page
            page = Page(
                document_id=document.id,
                page_num=1,
                text_content=doc_data["description"],
                text_quality=1.0,
                media_type="metadata_stub"
            )
            db.add(page)
            print(f"  ✓ Document: {doc_data['filename']}")
        
        print(f"\n✅ Created {len(documents_data)} sample documents\n")
        
        db.commit()
        
        print("="*60)
        print("✅ DATABASE SEEDING COMPLETE")
        print("="*60)
        print(f"Entities: {len(entity_map)}")
        print(f"Relationships: {len(relationships_data)}")
        print(f"Documents: {len(documents_data)}")
        print("\nDatabase ready for production deployment!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
