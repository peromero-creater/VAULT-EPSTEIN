"""
Enhanced Google Pinpoint Scraper
Fetches ALL documents from the Epstein Files collection
"""
import requests
import time
import re
from typing import List, Dict, Optional
from pathlib import Path
from bs4 import BeautifulSoup
import json
import sys

sys.path.append(str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session
from models import Document, Page, Entity, PageEntity, Relationship
from database import SessionLocal

class ComprehensivePinpointScraper:
    """
    Scrapes ALL documents from Google Pinpoint Epstein collection
    Collection ID: 061ce61c9e70bdfd
    """
    
    COLLECTION_ID = "061ce61c9e70bdfd"
    BASE_URL = "https://journaliststudio.google.com/pinpoint"
    SEARCH_URL = f"{BASE_URL}/search"
    
    def __init__(self, rate_limit_seconds: float = 2.0):
        self.rate_limit = rate_limit_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://journaliststudio.google.com/'
        })
        self.documents_scraped = []
        self.entities_found = set()
        self.locations_found = set()
        
    def fetch_collection_metadata(self) -> Dict:
        """Fetch collection overview to get total document count and facets"""
        print(f"🔍 Fetching collection metadata for {self.COLLECTION_ID}...")
        
        try:
            params = {
                'collection': self.COLLECTION_ID
            }
            response = self.session.get(self.SEARCH_URL, params=params, timeout=30)
            
            if response.status_code == 200:
                # Parse HTML to extract metadata
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to find total document count
                # Look for patterns like "52 documents" or similar
                doc_count_matches = re.findall(r'(\d+)\s+(?:documents|results|items)', response.text, re.IGNORECASE)
                total_docs = int(doc_count_matches[0]) if doc_count_matches else None
                
                # Extract location facets (from the screenshot, we know there are locations)
                locations = self._extract_locations_from_html(soup)
                
                # Extract person names/entities
                entities = self._extract_entities_from_html(soup)
                
                metadata = {
                    'collection_id': self.COLLECTION_ID,
                    'total_documents': total_docs,
                    'locations': locations,
                    'entities': entities,
                    'status': 'accessible'
                }
                
                print(f"✓ Collection metadata retrieved")
                if total_docs:
                    print(f"  Total documents: {total_docs}")
                print(f"  Locations found: {len(locations)}")
                print(f"  Entities found: {len(entities)}")
                
                return metadata
            else:
                print(f"⚠️  HTTP {response.status_code} - Collection may require authentication")
                return {'status': 'requires_auth', 'collection_id': self.COLLECTION_ID}
                
        except Exception as e:
            print(f"Error fetching metadata: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _extract_locations_from_html(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract location facets from HTML"""
        locations = []
        
        # Look for location elements (might be in a sidebar or filter panel)
        location_elements = soup.find_all(['div', 'li', 'span'], text=re.compile(r'Dubai|Singapore|Africa|Francisco', re.I))
        
        for elem in location_elements:
            # Try to extract location name and count
            text = elem.get_text(strip=True)
            # Look for pattern like "Dubai 52" or "Dubai (52)"
            match = re.match(r'([A-Za-z\s]+)\s*[\(]?(\d+)[\)]?', text)
            if match:
                name, count = match.groups()
                locations.append({
                    'name': name.strip(),
                    'document_count': int(count)
                })
        
        return locations
    
    def _extract_entities_from_html(self, soup: BeautifulSoup) -> List[str]:
        """Extract person/entity names from HTML"""
        entities = set()
        
        # Look for common name patterns
        # This is a heuristic approach
        text_content = soup.get_text()
        
        # Common patterns for names in Epstein documents
        name_patterns = [
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b',  # FirstName LastName
            r'\b(Jeffrey\s+Epstein|Ghislaine\s+Maxwell|Prince\s+Andrew)\b',  # Known names
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text_content)
            entities.update(matches)
        
        return list(entities)
    
    def search_by_location(self, location: str, limit: int = 100) -> List[Dict]:
        """Search for documents by location"""
        print(f"📍 Searching documents in location: {location}")
        
        try:
            params = {
                'collection': self.COLLECTION_ID,
                'q': location,  # Search query
                'location': location  # Location filter if available
            }
            
            response = self.session.get(self.SEARCH_URL, params=params, timeout=30)
            
            if response.status_code == 200:
                documents = self._parse_search_results(response.text, location)
                print(f"  Found {len(documents)} documents for {location}")
                return documents[:limit]
            else:
                print(f"  ⚠️  HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"  Error: {e}")
            return []
        
        finally:
            time.sleep(self.rate_limit)
    
    def search_by_entity(self, entity_name: str, limit: int = 100) -> List[Dict]:
        """Search for documents mentioning an entity"""
        print(f"👤 Searching documents for entity: {entity_name}")
        
        try:
            params = {
                'collection': self.COLLECTION_ID,
                'q': entity_name
            }
            
            response = self.session.get(self.SEARCH_URL, params=params, timeout=30)
            
            if response.status_code == 200:
                documents = self._parse_search_results(response.text, entity_name)
                print(f"  Found {len(documents)} documents mentioning {entity_name}")
                return documents[:limit]
            else:
                print(f"  ⚠️  HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"  Error: {e}")
            return []
        
        finally:
            time.sleep(self.rate_limit)
    
    def _parse_search_results(self, html: str, context: str = "") -> List[Dict]:
        """Parse search results from HTML response"""
        soup = BeautifulSoup(html, 'html.parser')
        documents = []
        
        # Try to find document links/cards
        # This is highly dependent on Pinpoint's HTML structure
        doc_elements = soup.find_all(['a', 'div'], class_=re.compile(r'document|result|item', re.I))
        
        for elem in doc_elements[:50]:  # Limit to prevent over-parsing
            try:
                # Extract document metadata
                title = elem.get('title') or elem.get_text(strip=True)[:100]
                href = elem.get('href')
                
                if title and len(title) > 5:
                    documents.append({
                        'title': title,
                        'url': f"{self.BASE_URL}{href}" if href and not href.startswith('http') else href,
                        'context': context,
                        'source': 'pinpoint'
                    })
            except Exception as e:
                continue
        
        return documents
    
    def scrape_all_documents(self, db: Session, limit_per_location: int = None) -> int:
        """
        Comprehensive scraping: fetch ALL documents from the collection
        """
        print("\n" + "="*70)
        print("COMPREHENSIVE PINPOINT SCRAPING - EPSTEIN FILES")
        print("="*70)
        
        # First, get collection metadata
        metadata = self.fetch_collection_metadata()
        
        if metadata.get('status') == 'requires_auth':
            print("\n⚠️  Collection requires authentication")
            print("Please export documents manually from Pinpoint UI")
            return 0
        
        total_ingested = 0
        
        # Strategy 1: Scrape by locations
        locations = metadata.get('locations', [])
        if locations:
            print(f"\n📍 Scraping by {len(locations)} locations...")
            for loc_data in locations:
                location = loc_data.get('name')
                doc_count = loc_data.get('document_count', 0)
                
                print(f"\n  Location: {location} ({doc_count} documents)")
                
                # Search documents for this location
                docs = self.search_by_location(location, limit=limit_per_location or doc_count)
                
                # Ingest each document
                for doc_data in docs:
                    try:
                        ingested = self._ingest_document(db, doc_data, location)
                        if ingested:
                            total_ingested += 1
                    except Exception as e:
                        print(f"    Error ingesting document: {e}")
                
                db.commit()
        
        # Strategy 2: Scrape by entities/persons
        entities = metadata.get('entities', [])
        if entities:
            print(f"\n👤 Scraping by {len(entities)} entities...")
            for entity in entities[:20]:  # Limit to top entities
                docs = self.search_by_entity(entity, limit=50)
                
                for doc_data in docs:
                    try:
                        ingested = self._ingest_document(db, doc_data, entity_context=entity)
                        if ingested:
                            total_ingested += 1
                    except Exception as e:
                        print(f"    Error: {e}")
                
                db.commit()
        
        # Strategy 3: General search for remaining documents
        print(f"\n🔍 General search for additional documents...")
        general_docs = self.search_by_entity("epstein", limit=200)
        
        for doc_data in general_docs:
            try:
                ingested = self._ingest_document(db, doc_data)
                if ingested:
                    total_ingested += 1
            except Exception as e:
                pass
        
        db.commit()
        
        print("\n" + "="*70)
        print(f"✅ SCRAPING COMPLETE: {total_ingested} documents ingested")
        print("="*70)
        
        return total_ingested
    
    def _ingest_document(self, db: Session, doc_data: Dict, location: str = None, entity_context: str = None) -> bool:
        """Ingest a single document into database"""
        
        title = doc_data.get('title', 'Untitled')
        url = doc_data.get('url', '')
        
        # Check if already exists
        existing = db.query(Document).filter(
            Document.filename == title
        ).first()
        
        if existing:
            return False
        
        # Create document record
        document = Document(
            filename=title[:512],
            path=url[:1024] if url else f"pinpoint/{self.COLLECTION_ID}/{title[:50]}",
            external_url=url[:2048] if url else None,
            doc_type="PDF",
            dataset="Pinpoint-Epstein"
        )
        
        db.add(document)
        db.flush()
        
        # Create a placeholder page with context
        context_text = f"Document from Pinpoint Epstein Files collection. "
        if location:
            context_text += f"Location: {location}. "
        if entity_context:
            context_text += f"Related to: {entity_context}. "
        context_text += f"Title: {title}"
        
        page = Page(
            document_id=document.id,
            page_num=1,
            text_content=context_text,
            text_quality=0.5,
            media_type='pinpoint_reference'
        )
        db.add(page)
        
        # If we have location, create/link location entity
        if location:
            location_entity = db.query(Entity).filter(
                Entity.name == location,
                Entity.type == "LOCATION"
            ).first()
            
            if not location_entity:
                location_entity = Entity(
                    name=location,
                    type="LOCATION",
                    normalized_name=location.upper()
                )
                db.add(location_entity)
                db.flush()
            
            # Link page to location
            page_entity = PageEntity(
                page_id=page.id,
                entity_id=location_entity.id,
                frequency=1
            )
            db.add(page_entity)
        
        # If we have entity context, create/link person entity
        if entity_context:
            person_entity = db.query(Entity).filter(
                Entity.name == entity_context,
                Entity.type == "PERSON"
            ).first()
            
            if not person_entity:
                person_entity = Entity(
                    name=entity_context,
                    type="PERSON",
                    normalized_name=entity_context.upper()
                )
                db.add(person_entity)
                db.flush()
            
            # Link page to person
            page_entity = PageEntity(
                page_id=page.id,
                entity_id=person_entity.id,
                frequency=1
            )
            db.add(page_entity)
        
        return True


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape ALL documents from Pinpoint Epstein collection')
    parser.add_argument('--limit-per-location', type=int, help='Limit documents per location (default: unlimited)')
    parser.add_argument('--test', action='store_true', help='Test mode: just fetch metadata')
    
    args = parser.parse_args()
    
    scraper = ComprehensivePinpointScraper()
    
    if args.test:
        # Just test metadata fetching
        metadata = scraper.fetch_collection_metadata()
        print("\n📊 Collection Metadata:")
        print(json.dumps(metadata, indent=2))
    else:
        # Full scraping
        db = SessionLocal()
        try:
            count = scraper.scrape_all_documents(db, limit_per_location=args.limit_per_location)
            print(f"\n🎉 Successfully ingested {count} documents from Pinpoint")
        finally:
            db.close()


if __name__ == "__main__":
    main()
