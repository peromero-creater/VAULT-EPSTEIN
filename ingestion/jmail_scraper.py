"""
jmail.world Document Scraper
Fetches documents from jmail.world/drive, /photos, /flights
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
from models import Document, Page, FlightLog, Entity
from database import SessionLocal

class JMailScraper:
    BASE_URL = "https://jmail.world"
    
    def __init__(self, rate_limit_seconds: float = 2.0):
        self.rate_limit = rate_limit_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_drive(self) -> List[Dict]:
        """Scrape documents from jmail.world/drive"""
        documents = []
        
        try:
            print(f"Scraping {self.BASE_URL}/drive...")
            response = self.session.get(f"{self.BASE_URL}/drive", timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find document links (adjust selectors based on actual page structure)
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Look for document-like links
                if any(ext in href.lower() for ext in ['.pdf', '.doc', '.txt', 'document', 'file']):
                    if not href.startswith('http'):
                        href = self.BASE_URL + href
                    
                    documents.append({
                        'title': text or Path(href).stem,
                        'url': href,
                        'type': 'DOCUMENT',
                        'source': 'jmail-drive'
                    })
            
            print(f"Found {len(documents)} documents in drive")
            
        except Exception as e:
            print(f"Error scraping jmail.world/drive: {e}")
        
        return documents
    
    def scrape_photos(self) -> List[Dict]:
        """Scrape photos/images from jmail.world/photos"""
        photos = []
        
        try:
            print(f"Scraping {self.BASE_URL}/photos...")
            response = self.session.get(f"{self.BASE_URL}/photos", timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find image links
            images = soup.find_all('img', src=True)
            
            for img in images:
                src = img.get('src', '')
                alt = img.get('alt', '')
                
                if not src.startswith('http'):
                    src = self.BASE_URL + src
                
                # Skip icons and UI elements
                if any(skip in src.lower() for skip in ['icon', 'logo', 'button']):
                    continue
                
                photos.append({
                    'title': alt or f"Photo_{len(photos)+1}",
                    'url': src,
                    'type': 'IMAGE',
                    'source': 'jmail-photos'
                })
            
            print(f"Found {len(photos)} photos")
            
        except Exception as e:
            print(f"Error scraping jmail.world/photos: {e}")
        
        return photos
    
    def scrape_flights(self) -> List[Dict]:
        """Scrape flight logs from jmail.world/flights"""
        flights = []
        
        try:
            print(f"Scraping {self.BASE_URL}/flights...")
            response = self.session.get(f"{self.BASE_URL}/flights", timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for flight records (adjust based on actual structure)
            # This might be in a table or list format
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 4:
                        flights.append({
                            'date': cells[0].get_text(strip=True),
                            'tail_number': cells[1].get_text(strip=True),
                            'route': cells[2].get_text(strip=True),
                            'passengers': cells[3].get_text(strip=True),
                            'source': 'jmail-flights'
                        })
            
            print(f"Found {len(flights)} flight records")
            
        except Exception as e:
            print(f"Error scraping jmail.world/flights: {e}")
        
        return flights
    
    def ingest_documents(
        self,
        db: Session,
        limit: int = 100,
        include_photos: bool = True,
        include_flights: bool = True
    ) -> int:
        """Ingest documents from jmail.world into database"""
        print("Starting jmail.world ingestion...")
        
        ingested_count = 0
        
        # Scrape drive documents
        drive_docs = self.scrape_drive()
        
        for doc_info in drive_docs[:limit]:
            try:
                url = doc_info['url']
                title = doc_info['title']
                
                # Check if exists
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
                    path=f"jmail_drive/{Path(url).name}",
                    external_url=url,
                    doc_type="DOCUMENT",
                    dataset="jmail.world-drive"
                )
                db.add(document)
                
                # Try to fetch content if it's accessible
                try:
                    content_resp = self.session.get(url, timeout=30)
                    if content_resp.status_code == 200 and 'text' in content_resp.headers.get('content-type', ''):
                        page = Page(
                            document_id=document.id,
                            page_num=1,
                            text_content=content_resp.text[:10000],  # Limit size
                            text_quality=0.7,
                            media_type='web_document'
                        )
                        db.add(page)
                except:
                    pass  # If we can't fetch content, just store the link
                
                db.commit()
                ingested_count += 1
                time.sleep(self.rate_limit)
                
            except Exception as e:
                print(f"Error ingesting {title}: {e}")
                db.rollback()
                continue
        
        # Ingest flight logs
        if include_flights:
            flights = self.scrape_flights()
            for flight in flights[:50]:  # Limit flights
                try:
                    existing = db.query(FlightLog).filter(
                        FlightLog.tail_number == flight['tail_number'],
                        FlightLog.date == flight['date']
                    ).first()
                    
                    if not existing:
                        flight_log = FlightLog(
                            tail_number=flight['tail_number'],
                            date=flight['date'],
                            origin=flight.get('route', '').split('-')[0] if '-' in flight.get('route', '') else '',
                            destination=flight.get('route', '').split('-')[-1] if '-' in flight.get('route', '') else '',
                            passengers=flight['passengers']
                        )
                        db.add(flight_log)
                        db.commit()
                except Exception as e:
                    print(f"Error ingesting flight: {e}")
                    db.rollback()
        
        print(f"\n✓ Ingestion complete: {ingested_count} documents added")
        return ingested_count


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest documents from jmail.world')
    parser.add_argument('--limit', type=int, default=50, help='Maximum documents to ingest')
    parser.add_argument('--rate-limit', type=float, default=2.0, help='Seconds between requests')
    parser.add_argument('--skip-photos', action='store_true', help='Skip photo ingestion')
    parser.add_argument('--skip-flights', action='store_true', help='Skip flight logs')
    
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        scraper = JMailScraper(rate_limit_seconds=args.rate_limit)
        count = scraper.ingest_documents(
            db=db,
            limit=args.limit,
            include_photos=not args.skip_photos,
            include_flights=not args.skip_flights
        )
        print(f"\n🎉 Successfully ingested {count} items from jmail.world")
    finally:
        db.close()


if __name__ == "__main__":
    main()
