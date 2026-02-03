import requests
import os
import sqlite3
import shutil
from datetime import datetime
from models import Document, Page
from database import SessionLocal, engine
from sqlalchemy.orm import Session

# Configuration
ARCHIVE_BASE = "https://archive.org/download/combined-all-epstein-files"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "files")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault_epstein.db")

# The 11 Main Datasets from Archive.org
DATASETS = [
    {
        "name": "1332-16",
        "pdf": "1332-16.pdf",
        "txt": "1332-16_djvu.txt"
    },
    {
        "name": "DataSet_1_COMPLETE",
        "pdf": "DataSet_1_COMPLETE.pdf",
        "txt": "DataSet_1_COMPLETE_djvu.txt"
    },
    {
        "name": "DataSet_2_COMPLETE",
        "pdf": "DataSet_2_COMPLETE.pdf",
        "txt": "DataSet_2_COMPLETE_djvu.txt"
    },
    {
        "name": "DataSet_3_COMPLETE",
        "pdf": "DataSet_3_COMPLETE.pdf",
        "txt": "DataSet_3_COMPLETE_djvu.txt"
    },
    {
        "name": "DataSet_4_COMPLETE",
        "pdf": "DataSet_4_COMPLETE.pdf",
        "txt": "DataSet_4_COMPLETE_djvu.txt"
    },
    {
        "name": "DataSet_5_COMPLETE",
        "pdf": "DataSet_5_COMPLETE.pdf",
        "txt": "DataSet_5_COMPLETE_djvu.txt"
    },
    {
        "name": "DataSet_6_COMPLETE",
        "pdf": "DataSet_6_COMPLETE.pdf",
        "txt": "DataSet_6_COMPLETE_djvu.txt"
    },
    {
        "name": "DataSet_7_COMPLETE",
        "pdf": "DataSet_7_COMPLETE.pdf",
        "txt": "DataSet_7_COMPLETE_djvu.txt"
    },
    {
        "name": "DataSet_8_COMPLETE",
        "pdf": "DataSet_8_COMPLETE.pdf",
        "txt": "https://archive.org/stream/combined-all-epstein-files/DataSet%208/VOL00008/IMAGES/0001/EFTA00009676_djvu.txt"
    },
    {
        "name": "COMBINED_ALL_EPSTEIN_FILES",
        "pdf": "COMBINED_ALL_EPSTEIN_FILES.pdf",
        "txt": "COMBINED_ALL_EPSTEIN_FILES_djvu.txt"
    },
    {
        "name": "EFTA00009676",
        "pdf": "DataSet%208/VOL00008/IMAGES/0001/EFTA00009676.pdf",
        "txt": "DataSet%208/VOL00008/IMAGES/0001/EFTA00009676_djvu.txt"
    }
]

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def download_file(url, dest_path):
    if os.path.exists(dest_path):
        print(f"   [SKIP] Already exists: {dest_path}")
        return True
    
    print(f"   [DOWN] Downloading {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("   [DONE] Download complete.")
        return True
    except Exception as e:
        print(f"   [ERR] Failed to download: {e}")
        return False

def ingest_dataset(db: Session, ds):
    print(f"\nProcessing Dataset: {ds['name']}")
    
    # 1. Download Text
    txt_filename = os.path.basename(ds['txt'])
    txt_url = f"{ARCHIVE_BASE}/{ds['txt']}" if "http" not in ds['txt'] else ds['txt']
    txt_local_path = os.path.join(DATA_DIR, txt_filename)
    
    ensure_dir(DATA_DIR)
    
    if download_file(txt_url, txt_local_path):
        try:
            with open(txt_local_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Create DB Entry
            existing_doc = db.query(Document).filter(Document.filename == ds['name']).first()
            
            if not existing_doc:
                print(f"   [DB] Creating Document entry for {ds['name']}...")
                new_doc = Document(
                    filename=ds['name'],
                    path=os.path.join("data", "files", os.path.basename(ds['pdf'])),
                    doc_type="pdf",
                    dataset="Archive.org Ingest",
                    added_at=datetime.now(),
                    external_url=f"{ARCHIVE_BASE}/{ds['pdf']}"
                )
                db.add(new_doc)
                db.commit()
                db.refresh(new_doc)
                
                # Create Page 1 with the full content
                print(f"   [DB] Creating Page entry with {len(content)} chars...")
                new_page = Page(
                    document_id=new_doc.id,
                    page_num=1,
                    text_content=content,
                    text_quality=1.0,
                    media_type="full_text_import"
                )
                db.add(new_page)
                db.commit()
            else:
                print(f"   [DB] Entry already exists.")
                
        except Exception as e:
            print(f"   [ERR] Error saving to DB: {e}")

    # 2. Download PDF (Background/Optional) - SLOW
    pdf_filename = os.path.basename(ds['pdf'])
    pdf_url = f"{ARCHIVE_BASE}/{ds['pdf']}"
    pdf_local_path = os.path.join(DATA_DIR, pdf_filename)
    
    # Check if download is needed (don't re-download if exists)
    if not os.path.exists(pdf_local_path):
        print(f"   [PDF] Queueing PDF download: {pdf_filename} (This might take a while)")
        download_file(pdf_url, pdf_local_path)
    else:
         print(f"   [SKIP] PDF already exists: {pdf_filename}")

if __name__ == "__main__":
    print("🚀 STARTING ARCHIVE.ORG INGESTION")
    print("--------------------------------")
    
    db = SessionLocal()
    try:
        for ds in DATASETS:
            ingest_dataset(db, ds)
    finally:
        db.close()
    
    print("\n✅ INGESTION COMPLETE!")
