"""
Google Journalist Studio Pinpoint Integration
Fetches documents from Pinpoint collections
"""
import requests
import time
from typing import List, Dict
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session
from models import Document, Page
from database import SessionLocal

class PinpointFetcher:
    """
    Google Pinpoint integration
    Note: This requires Google Cloud authentication
    """
    
    # The collection ID from the URL provided
    COLLECTION_ID = "c109fa8e7dcf42c1"
    PINPOINT_SEARCH_URL = "https://journaliststudio.google.com/pinpoint/search"
    
    def __init__(self, rate_limit_seconds: float = 1.5):
        self.rate_limit = rate_limit_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_documents(self, query: str = "epstein", limit: int = 100) -> List[Dict]:
        """
        Search Pinpoint collection
        Note: This is a simplified version. Full integration would require:
        - Google Cloud credentials
        - Pinpoint API access
        - OAuth authentication
        
        For now, this provides the structure for future implementation
        """
        documents = []
        
        print(f"Searching Pinpoint collection {self.COLLECTION_ID}...")
        print("⚠️  Note: Full Pinpoint integration requires Google Cloud authentication")
        print("   This is a placeholder that demonstrates the structure needed.")
        
        # Placeholder for actual API integration
        # In production, you would:
        # 1. Authenticate with Google Cloud
        # 2. Use Pinpoint API to search collection
        # 3. Download document content
        # 4. Extract text and metadata
        
        try:
            # Attempt to access the public search interface
            # (May require authentication in practice)
            params = {
                'collection': self.COLLECTION_ID,
                'q': query
            }
            
            response = self.session.get(
                self.PINPOINT_SEARCH_URL,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✓ Connected to Pinpoint (status: {response.status_code})")
                print("  Manual export may be required for full document access")
            else:
                print(f"⚠️  Pinpoint access requires authentication (status: {response.status_code})")
            
        except Exception as e:
            print(f"Pinpoint connection: {e}")
            print("  Recommendation: Export documents manually from Pinpoint UI")
        
        return documents
    
    def ingest_from_export(
        self,
        db: Session,
        export_directory: Path,
        dataset_name: str = "Pinpoint-Epstein"
    ) -> int:
        """
        Ingest documents from a Pinpoint manual export
        
        Usage:
        1. Go to https://journaliststudio.google.com/pinpoint/
        2. Open collection c109fa8e7dcf42c1
        3. Export documents to a folder
        4. Run this function pointing to that folder
        """
        print(f"Ingesting from Pinpoint export: {export_directory}")
        
        if not export_directory.exists():
            print(f"❌ Directory not found: {export_directory}")
            print("   Please export documents from Pinpoint UI first")
            return 0
        
        ingested_count = 0
        
        # Process all PDFs and text files in export directory
        for file_path in export_directory.glob('**/*'):
            if file_path.suffix.lower() in ['.pdf', '.txt', '.doc', '.docx']:
                try:
                    # Check if already exists
                    existing = db.query(Document).filter(
                        Document.filename == file_path.name
                    ).first()
                    
                    if existing:
                        continue
                    
                    print(f"Ingesting: {file_path.name}")
                    
                    # Create document
                    document = Document(
                        filename=file_path.name,
                        path=str(file_path),
                        external_url=f"https://journaliststudio.google.com/pinpoint/collections/{self.COLLECTION_ID}",
                        doc_type="PDF" if file_path.suffix == '.pdf' else "DOCUMENT",
                        dataset=dataset_name
                    )
                    db.add(document)
                    db.flush()
                    
                    # Extract text based on file type
                    if file_path.suffix == '.txt':
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                            page = Page(
                                document_id=document.id,
                                page_num=1,
                                text_content=text,
                                text_quality=0.9,
                                media_type='text_doc'
                            )
                            db.add(page)
                    
                    elif file_path.suffix == '.pdf':
                        try:
                            from PyPDF2 import PdfReader
                            reader = PdfReader(file_path)
                            for page_num, pdf_page in enumerate(reader.pages, 1):
                                text = pdf_page.extract_text()
                                if text.strip():
                                    page = Page(
                                        document_id=document.id,
                                        page_num=page_num,
                                        text_content=text,
                                        text_quality=0.7,
                                        media_type='pdf_page'
                                    )
                                    db.add(page)
                        except Exception as e:
                            print(f"  Error extracting PDF: {e}")
                    
                    db.commit()
                    ingested_count += 1
                    
                except Exception as e:
                    print(f"Error ingesting {file_path.name}: {e}")
                    db.rollback()
        
        print(f"\n✓ Ingestion complete: {ingested_count} documents from Pinpoint")
        return ingested_count


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest from Google Pinpoint')
    parser.add_argument('--export-dir', type=str, help='Path to Pinpoint export directory')
    parser.add_argument('--search', type=str, default='epstein', help='Search query (requires auth)')
    
    args = parser.parse_args()
    
    db = SessionLocal()
    fetcher = PinpointFetcher()
    
    try:
        if args.export_dir:
            # Ingest from manual export
            export_path = Path(args.export_dir)
            count = fetcher.ingest_from_export(db, export_path)
            print(f"\n🎉 Successfully ingested {count} documents from Pinpoint export")
        else:
            # Show search capability (requires auth)
            docs = fetcher.search_documents(args.search)
            print(f"\nFound {len(docs)} documents")
            print("\n📌 To ingest Pinpoint documents:")
            print("   1. Export from Pinpoint UI to a folder")
            print("   2. Run: python pinpoint_fetcher.py --export-dir /path/to/export")
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
