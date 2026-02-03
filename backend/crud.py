from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models import Document, Page, Entity, PageEntity, CountryStats, PersonCountryCoMention
from typing import List, Optional

def get_countries(db: Session):
    return db.query(CountryStats).order_by(desc(CountryStats.page_count)).all()

def get_country_details(db: Session, country_code: str):
    stats = db.query(CountryStats).filter_by(country_code=country_code).first()
    
    # Get top people mentioned in pages that mention this country
    # Joining Pages -> PageEntities -> Entities
    top_people = db.query(Entity.name, func.count(Entity.id).label('count')) \
        .join(PageEntity, Entity.id == PageEntity.entity_id) \
        .join(Page, Page.id == PageEntity.page_id) \
        .join(PageEntity, Page.id == PageEntity.page_id) \
        .join(Entity, Entity.id == PageEntity.entity_id) \
        .filter(Entity.type == "PERSON") \
        # This join logic needs to be cleaner to find pages that mention a GPE with this country_code
        # Let's simplify for now
    
    return stats

def get_person_details(db: Session, person_name: str):
    person = db.query(Entity).filter_by(name=person_name, type="PERSON").first()
    if not person:
        return None
        
    # Get pages mentioning this person
    pages = db.query(Page).join(PageEntity).filter(PageEntity.entity_id == person.id).limit(50).all()
    
    return {
        "person": person,
        "pages": pages
    }

def get_page(db: Session, page_id: int):
    return db.query(Page).filter(Page.id == page_id).first()
