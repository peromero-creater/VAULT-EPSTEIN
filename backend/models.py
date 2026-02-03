from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, DateTime, Table, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    filename = Column(String(512), nullable=False)
    path = Column(String(1024), nullable=False)
    external_url = Column(String(2048)) # Link to jmail.world, DocumentCloud, etc.
    doc_type = Column(String(50)) # PDF, Image, Video
    dataset = Column(String(100))
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # AI Analysis fields
    ai_analyzed = Column(Integer, default=0)  # Boolean: has this been analyzed by AI?
    ai_summary = Column(Text)  # AI-generated summary
    
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")

class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    page_num = Column(Integer)
    text_content = Column(Text) # PII Masked
    text_quality = Column(Float) # OCR confidence
    media_type = Column(String(50)) # page_image, transcript_stub
    
    # Full-Text Search will use text_content directly
    # For Postgres, we can add a GIN index on text_content
    
    document = relationship("Document", back_populates="pages")
    entities = relationship("PageEntity", back_populates="page")

    # DB-agnostic Index (will be ignored by SQLite but valid in SQLAlchemy)
    # On Postgres it will create a standard index on text_content
    __table_args__ = (
        Index('ix_page_text_content', 'text_content'),
    )

class Entity(Base):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50)) # PERSON, ORG, GPE, LOC
    normalized_name = Column(String(255))
    country_code = Column(String(10)) # For normalized countries
    
    __table_args__ = (UniqueConstraint('name', 'type', name='_name_type_uc'),)

class PageEntity(Base):
    __tablename__ = "page_entities"
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.id"))
    entity_id = Column(Integer, ForeignKey("entities.id"))
    frequency = Column(Integer, default=1)
    
    page = relationship("Page", back_populates="entities")
    entity = relationship("Entity")

class CountryStats(Base):
    __tablename__ = "country_stats"
    id = Column(Integer, primary_key=True)
    country_code = Column(String(10), unique=True)
    doc_count = Column(Integer, default=0)
    page_count = Column(Integer, default=0)

class PersonCountryCoMention(Base):
    __tablename__ = "person_country_comention"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("entities.id"))
    country_code = Column(String(10))
    frequency = Column(Integer, default=0)

class FlightLog(Base):
    __tablename__ = "flight_logs"
    id = Column(Integer, primary_key=True)
    tail_number = Column(String(50))
    date = Column(DateTime)
    origin = Column(String(100))
    destination = Column(String(100))
    passengers = Column(Text) # JSON list or comma separated
    doc_reference = Column(Integer, ForeignKey("documents.id"))

class AINarrative(Base):
    __tablename__ = "ai_narratives"
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    content = Column(Text)
    narrative_type = Column(String(50)) # STORY, SUMMARY, CONNECTION
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Links to entities involved
    entities = relationship("NarrativeEntity", back_populates="narrative")

class NarrativeEntity(Base):
    __tablename__ = "narrative_entities"
    id = Column(Integer, primary_key=True)
    narrative_id = Column(Integer, ForeignKey("ai_narratives.id"))
    entity_id = Column(Integer, ForeignKey("entities.id"))
    
    narrative = relationship("AINarrative", back_populates="entities")
    entity = relationship("Entity")

class Relationship(Base):
    __tablename__ = "relationships"
    id = Column(Integer, primary_key=True)
    source_entity_id = Column(Integer, ForeignKey("entities.id"))
    target_entity_id = Column(Integer, ForeignKey("entities.id"))
    rel_type = Column(String(100)) # e.g., "CO-PASSENGER", "ASSOCIATE", "EMPLOYEE"
    description = Column(Text)
    evidence_page_id = Column(Integer, ForeignKey("pages.id"))
    confidence_score = Column(Float, default=0.5)  # AI confidence in this relationship

