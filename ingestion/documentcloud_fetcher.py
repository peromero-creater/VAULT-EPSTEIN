"""
DocumentCloud API Integration
Fetches Epstein-related documents from DocumentCloud
"""
import requests
import time
from typing import List, Dict, Optional
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session
from models import Document, Page
from database import SessionLocal

class DocumentCloudFetcher:
    BASE_URL = "https://api.www.documentcloud.org/api"
    
    def __init__(self, rate_limit_seconds: float = 1.0):
        self.rate_limit = rate_limit_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VaultEpstein/1.0 (Research Archive)'
        })
    
    def search_documents(self, query: str = "epstein", limit: int = 100) -> List[Dict]:
        """Search for documents on DocumentCloud"""
        documents = []
        page = 1
        per_page = 25  # DocumentCloud API limit
        
        while len(documents) < limit:
            print(f"Fetching page {page} from DocumentCloud...")
            
            params = {
                'q': query,
                'page': page,
                'per_page': per_page,
                'expand': 'sections,notes'
            }
            
            try:
                response = self.session.get(
                    f"{self.BASE_URL}/documents/search/",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', [])
                if not results:
                    break
                
                documents.extend(results)
                
                # Check if we have more pages
                if not data.get('next'):
                    break
                    
                page += 1
                time.sleep(self.rate_limit)
                
            except Exception as e:
                print(f"Error fetching from DocumentCloud: {e}")
                break
        
        return documents[:limit]
    
    def fetch_document_text(self, document_id: str, doc_url: str) -> List[Dict]:
        """Fetch full text for a document, page by page"""
        pages = []
        
        try:
            # Try to get the full text endpoint
            text_url = f"{self.BASE_URL}/documents/{document_id}/text/"
            response = self.session.get(text_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # DocumentCloud returns pages as a dict with page numbers as keys
                for page_num, text in data.items():
                    if text and text.strip():
                        pages.append({
                            'page_num': int(page_num),
                            'text': text,
                            'quality': 0.8  # Assume good quality from DocumentCloud
                        })
            
            time.sleep(self.rate_limit)
            
        except Exception as e:
            print(f"Error fetching text for document {document_id}: {e}")
        
        return pages
    
    def ingest_documents(
        self, 
        db: Session, 
        query: str = "epstein", 
        limit: int = 100,
        dataset_name: str = "DocumentCloud"
    ) -> int:
        """Ingest documents from DocumentCloud into database"""
        print(f"Starting DocumentCloud ingestion (limit={limit})...")
        
        # Search for documents
        dc_documents = self.search_documents(query, limit)
        print(f"Found {len(dc_documents)} documents")
        
        ingested_count = 0
        
        for dc_doc in dc_documents:
            try:
                doc_id = dc_doc.get('id')
                title = dc_doc.get('title', 'Untitled')
                canonical_url = dc_doc.get('canonical_url', '')
                page_count = dc_doc.get('page_count', 0)
                
                # Check if document already exists
                existing = db.query(Document).filter(
                    Document.external_url == canonical_url
                ).first()
                
                if existing:
                    print(f"Skipping {title} (already exists)")
                    continue
                
                print(f"Ingesting: {title} ({page_count} pages)")
                
                # Create document record
                document = Document(
                    filename=title,
                    path=f"documentcloud/{doc_id}",
                    external_url=canonical_url,
                    doc_type="PDF",
                    dataset=dataset_name
                )
                db.add(document)
                db.flush()  # Get the ID
                
                # Fetch and store pages
                pages = self.fetch_document_text(doc_id, canonical_url)
                
                for page_data in pages:
                    page = Page(
                        document_id=document.id,
                        page_num=page_data['page_num'],
                        text_content=page_data['text'],
                        text_quality=page_data['quality'],
                        media_type='document_page'
                    )
                    db.add(page)
                
                db.commit()
                ingested_count += 1
                print(f"✓ Ingested {title} with {len(pages)} pages")
                
            except Exception as e:
                print(f"Error ingesting document: {e}")
                db.rollback()
                continue
        
        print(f"\n✓ Ingestion complete: {ingested_count} documents added")
        return ingested_count


def main():
    """CLI entry point for DocumentCloud ingestion"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest documents from DocumentCloud')
    parser.add_argument('--query', default='epstein', help='Search query')
    parser.add_argument('--limit', type=int, default=50, help='Maximum documents to ingest')
    parser.add_argument('--rate-limit', type=float, default=1.0, help='Seconds between requests')
    
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        fetcher = DocumentCloudFetcher(rate_limit_seconds=args.rate_limit)
        count = fetcher.ingest_documents(
            db=db,
            query=args.query,
            limit=args.limit
        )
        print(f"\n🎉 Successfully ingested {count} documents from DocumentCloud")
    finally:
        db.close()


if __name__ == "__main__":
    main()
