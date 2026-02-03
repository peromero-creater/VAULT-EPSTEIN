from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, DateTime, Table, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    filename = Column(String(512), nullable=False)
    path = Column(String(1024), nullable=False)
    doc_type = Column(String(50)) # PDF, Image, Video
    dataset = Column(String(100))
    added_at = Column(DateTime, default=datetime.utcnow)
    
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")

class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    page_num = Column(Integer)
    text_content = Column(Text) # PII Masked
    text_quality = Column(Float) # OCR confidence
    media_type = Column(String(50)) # page_image, transcript_stub
    
    document = relationship("Document", back_populates="pages")
    entities = relationship("PageEntity", back_populates="page")

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
