from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models import Document, Page, Entity, PageEntity, CountryStats, PersonCountryCoMention, FlightLog, AINarrative, Relationship
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

def get_flights(db: Session, limit: int = 100):
    return db.query(FlightLog).order_by(desc(FlightLog.date)).limit(limit).all()

def get_narratives(db: Session, narrative_type: Optional[str] = None):
    query = db.query(AINarrative)
    if narrative_type:
        query = query.filter(AINarrative.narrative_type == narrative_type)
    return query.order_by(desc(AINarrative.created_at)).all()

def get_relationships(db: Session, entity_id: int):
    return db.query(Relationship).filter(
        (Relationship.source_entity_id == entity_id) | 
        (Relationship.target_entity_id == entity_id)
    ).all()

def get_person_details_enhanced(db: Session, person_name: str):
    person = db.query(Entity).filter_by(name=person_name, type="PERSON").first()
    if not person:
        return None
        
    pages = db.query(Page).join(PageEntity).filter(PageEntity.entity_id == person.id).limit(20).all()
    relationships = get_relationships(db, person.id)
    
    return {
        "person": person,
        "pages": pages,
        "relationships": relationships
    }

