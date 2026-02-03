"""
Unified Document Ingestion Script
Orchestrates all document sources
"""
import argparse
import sys
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from database import SessionLocal
from documentcloud_fetcher import DocumentCloudFetcher
from justice_gov_scraper import JusticeGovScraper
from jmail_scraper import JMailScraper
from pinpoint_fetcher import PinpointFetcher

def main():
    parser = argparse.ArgumentParser(description='Ingest documents from various sources')
    parser.add_argument(
        '--source',
        choices=['documentcloud', 'justice', 'jmail', 'pinpoint', 'all'],
        default='all',
        help='Which source to ingest from'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum documents to ingest per source'
    )
    parser.add_argument(
        '--query',
        default='epstein',
        help='Search query (for DocumentCloud)'
    )
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=1.5,
        help='Seconds between requests'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test without actually adding to database'
    )
    parser.add_argument(
        '--pinpoint-export',
        type=str,
        help='Path to Pinpoint export directory'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("VAULT EPSTEIN - DOCUMENT INGESTION")
    print("="*60)
    print(f"Source: {args.source}")
    print(f"Limit per source: {args.limit}")
    print(f"Rate limit: {args.rate_limit}s")
    print(f"Dry run: {args.dry_run}")
    print("="*60)
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No database changes will be made\n")
    
    db = SessionLocal()
    total_ingested = 0
    
    try:
        # DocumentCloud
        if args.source in ['documentcloud', 'all']:
            print("\n📄 DOCUMENTCLOUD INGESTION")
            print("-" * 60)
            fetcher = DocumentCloudFetcher(rate_limit_seconds=args.rate_limit)
            
            if not args.dry_run:
                count = fetcher.ingest_documents(
                    db=db,
                    query=args.query,
                    limit=args.limit
                )
                total_ingested += count
                print(f"✅ DocumentCloud: {count} documents ingested\n")
            else:
                docs = fetcher.search_documents(args.query, limit=min(5, args.limit))
                print(f"Found {len(docs)} documents (showing first 5):")
                for doc in docs[:5]:
                    print(f"  - {doc.get('title', 'Untitled')}")
                print()
        
        # Justice.gov
        if args.source in ['justice', 'all']:
            print("\n⚖️  JUSTICE.GOV INGESTION")
            print("-" * 60)
            scraper = JusticeGovScraper(rate_limit_seconds=args.rate_limit)
            
            if not args.dry_run:
                count = scraper.ingest_documents(
                    db=db,
                    limit=args.limit
                )
                total_ingested += count
                print(f"✅ Justice.gov: {count} documents ingested\n")
            else:
                docs = scraper.scrape_document_list()
                print(f"Found {len(docs)} documents (showing first 5):")
                for doc in docs[:5]:
                    print(f"  - {doc.get('title', 'Untitled')}")
                print()
        
        # jmail.world
        if args.source in ['jmail', 'all']:
            print("\n📧 JMAIL.WORLD INGESTION")
            print("-" * 60)
            scraper = JMailScraper(rate_limit_seconds=args.rate_limit)
            
            if not args.dry_run:
                count = scraper.ingest_documents(
                    db=db,
                    limit=args.limit
                )
                total_ingested += count
                print(f"✅ jmail.world: {count} items ingested\n")
            else:
                docs = scraper.scrape_drive()
                print(f"Found {len(docs)} documents in drive (showing first 5):")
                for doc in docs[:5]:
                    print(f"  - {doc.get('title', 'Untitled')}")
                print()
        
        # Google Pinpoint
        if args.source in ['pinpoint', 'all']:
            print("\n📌 GOOGLE PINPOINT INGESTION")
            print("-" * 60)
            fetcher = PinpointFetcher(rate_limit_seconds=args.rate_limit)
            
            if args.pinpoint_export:
                if not args.dry_run:
                    count = fetcher.ingest_from_export(
                        db=db,
                        export_directory=Path(args.pinpoint_export)
                    )
                    total_ingested += count
                    print(f"✅ Pinpoint: {count} documents ingested\n")
                else:
                    print(f"Would ingest from: {args.pinpoint_export}")
            else:
                print("⚠️  Pinpoint requires manual export")
                print("   1. Visit https://journaliststudio.google.com/pinpoint/")
                print("   2. Open collection c109fa8e7dcf42c1")
                print("   3. Export documents to a folder")
                print("   4. Run: python ingest_all.py --source pinpoint --pinpoint-export /path/to/folder\n")
        
        print("\n" + "="*60)
        if not args.dry_run:
            print(f"🎉 INGESTION COMPLETE: {total_ingested} total documents added")
        else:
            print("🔍 DRY RUN COMPLETE - No changes made")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Ingestion interrupted by user")
        print("Progress has been saved to database")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
