"""
Simple Local PDF Ingester
Ingests PDFs from data/files into the vault database
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from database import SessionLocal, init_db
from models import Document, Page
from PyPDF2 import PdfReader
import os

def ingest_local_pdfs():
    """Ingest all PDFs from data/files directory"""
    
    # Initialize database
    init_db()
    db = SessionLocal()
    
    # Find all PDFs
    data_dir = Path(__file__).parent.parent / "data" / "files"
    pdf_files = list(data_dir.glob("*.pdf"))
    
    print(f"\n{'='*60}")
    print(f"INGESTING LOCAL PDFs")
    print(f"{'='*60}")
    print(f"Found {len(pdf_files)} PDF files in {data_dir}\n")
    
    ingested_count = 0
    
    for pdf_path in pdf_files:
        try:
            # Check if already exists
            existing = db.query(Document).filter(
                Document.filename == pdf_path.name
            ).first()
            
            if existing:
                print(f"⏭️  Skipping (already exists): {pdf_path.name}")
                continue
            
            print(f"📄 Processing: {pdf_path.name}")
            
            # Create document record
            document = Document(
                filename=pdf_path.name,
                path=str(pdf_path),
                external_url=None,
                doc_type="PDF",
                dataset="Local-Epstein-Files"
            )
            db.add(document)
            db.flush()
            
            # Extract text from PDF
            try:
                reader = PdfReader(str(pdf_path))
                pages_extracted = 0
                
                for page_num, pdf_page in enumerate(reader.pages, 1):
                    try:
                        text = pdf_page.extract_text()
                        if text and text.strip():
                            page = Page(
                                document_id=document.id,
                                page_num=page_num,
                                text_content=text[:10000],  # Limit to 10k chars per page
                                text_quality=0.7,
                                media_type='pdf_page'
                            )
                            db.add(page)
                            pages_extracted += 1
                    except Exception as e:
                        print(f"  ⚠️  Error extracting page {page_num}: {e}")
                        continue
                
                db.commit()
                ingested_count += 1
                print(f"  ✅ Ingested {pages_extracted} pages")
                
            except Exception as e:
                print(f"  ❌ Error reading PDF: {e}")
                db.rollback()
                continue
                
        except Exception as e:
            print(f"  ❌ Error processing {pdf_path.name}: {e}")
            db.rollback()
            continue
    
    db.close()
    
    print(f"\n{'='*60}")
    print(f"✅ INGESTION COMPLETE")
    print(f"{'='*60}")
    print(f"Successfully ingested: {ingested_count} documents")
    print(f"Total documents in database: {ingested_count}")
    print(f"\nTo view: http://localhost:3000/search")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    ingest_local_pdfs()
