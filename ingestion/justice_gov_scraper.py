"""
Justice.gov Epstein Documents Scraper
Scrapes documents from https://www.justice.gov/epstein
"""
import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict
from pathlib import Path
import sys
import re
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session
from models import Document, Page
from database import SessionLocal

class JusticeGovScraper:
    BASE_URL = "https://www.justice.gov"
    EPSTEIN_URL = "https://www.justice.gov/epstein"
    
    def __init__(self, rate_limit_seconds: float = 2.0):
        self.rate_limit = rate_limit_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_document_list(self) -> List[Dict]:
        """Scrape the main Epstein page for document links"""
        documents = []
        
        try:
            print(f"Scraping {self.EPSTEIN_URL}...")
            response = self.session.get(self.EPSTEIN_URL, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all PDF links or document links
            links = soup.find_all('a', href=re.compile(r'\.(pdf|PDF)'))
            
            for link in links:
                href = link.get('href', '')
                if not href:
                    continue
                
                # Make absolute URL
                if href.startswith('/'):
                    href = self.BASE_URL + href
                elif not href.startswith('http'):
                    continue
                
                # Extract title
                title = link.get_text(strip=True) or link.get('title', '')
                if not title:
                    title = Path(href).stem
                
                documents.append({
                    'title': title,
                    'url': href,
                    'type': 'PDF'
                })
            
            print(f"Found {len(documents)} documents on justice.gov")
            
        except Exception as e:
            print(f"Error scraping justice.gov: {e}")
        
        return documents
    
    def download_pdf_text(self, url: str) -> List[Dict]:
        """Download and extract text from PDF"""
        pages = []
        
        try:
            from PyPDF2 import PdfReader
            from io import BytesIO
            
            print(f"Downloading PDF: {url}")
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            # Parse PDF
            pdf_file = BytesIO(response.content)
            reader = PdfReader(pdf_file)
            
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text and text.strip():
                    pages.append({
                        'page_num': page_num,
                        'text': text,
                        'quality': 0.7  # OCR quality estimate
                    })
            
            print(f"Extracted {len(pages)} pages")
            time.sleep(self.rate_limit)
            
        except Exception as e:
            print(f"Error downloading PDF {url}: {e}")
        
        return pages
    
    def ingest_documents(
        self,
        db: Session,
        limit: int = 100,
        dataset_name: str = "Justice.gov"
    ) -> int:
        """Ingest documents from justice.gov into database"""
        print("Starting justice.gov ingestion...")
        
        # Scrape document list
        doc_list = self.scrape_document_list()
        doc_list = doc_list[:limit]  # Apply limit
        
        ingested_count = 0
        
        for doc_info in doc_list:
            try:
                url = doc_info['url']
                title = doc_info['title']
                
                # Check if already exists
                existing = db.query(Document).filter(
                    Document.external_url == url
                ).first()
                
                if existing:
                    print(f"Skipping {title} (already exists)")
                    continue
                
                print(f"Ingesting: {title}")
                
                # Create document record
                document = Document(
                    filename=title,
                    path=f"justice_gov/{Path(url).name}",
                    external_url=url,
                    doc_type="PDF",
                    dataset=dataset_name
                )
                db.add(document)
                db.flush()
                
                # Download and extract text
                pages = self.download_pdf_text(url)
                
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
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest documents from justice.gov')
    parser.add_argument('--limit', type=int, default=50, help='Maximum documents to ingest')
    parser.add_argument('--rate-limit', type=float, default=2.0, help='Seconds between requests')
    
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        scraper = JusticeGovScraper(rate_limit_seconds=args.rate_limit)
        count = scraper.ingest_documents(db=db, limit=args.limit)
        print(f"\n🎉 Successfully ingested {count} documents from justice.gov")
    finally:
        db.close()


if __name__ == "__main__":
    main()
