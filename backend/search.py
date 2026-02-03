import os
from sqlalchemy import func
from sqlalchemy.orm import Session
from models import Page, Document
from database import SessionLocal

def search_pages(query: str, db: Session = None, filters: dict = None, limit: int = 10):
    """
    Search pages using a database-agnostic LIKE search (fallback) 
    or optimized Full-Text Search if on Postgres.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        # Check if we are on Postgres to use TSearch, else fallback to LIKE
        dialect = db.bind.dialect.name
        
        if dialect == "postgresql":
            # Postgres optimized search
            search_query = func.plainto_tsquery('english', query)
            # Note: We'd use the search_vector if we add it back, 
            # for now we search text_content directly
            q = db.query(Page).filter(func.to_tsvector('english', Page.text_content).op('@@')(search_query))
            q = q.order_by(func.ts_rank(func.to_tsvector('english', Page.text_content), search_query).desc())
        else:
            # SQLite / Generic fallback
            q = db.query(Page).filter(Page.text_content.ilike(f"%{query}%"))
        
        results = q.limit(limit).all()
        
        hits = []
        for page in results:
            hits.append({
                "_id": f"page_{page.id}",
                "_score": 1.0, 
                "_source": {
                    "text": page.text_content,
                    "page_id": page.id,
                    "document_id": page.document_id,
                }
            })
        return hits
    except Exception as e:
        print(f"Search failed: {e}")
        return []
    finally:
        if should_close:
            db.close()

# Mock functions for compatibility
def index_page(*args, **kwargs): pass
def index_narrative(*args, **kwargs): pass
def index_flight(*args, **kwargs): pass
def create_index(): pass
