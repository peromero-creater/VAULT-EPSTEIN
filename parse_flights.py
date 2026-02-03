import re
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Document, Page, FlightLog

# Connect to DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/vault_epstein.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def parse_flight_logs():
    print("Fetching JMail Flight Log document...")
    # Get JMail document pages
    # Try finding by filename first
    doc = db.query(Document).filter(Document.filename.ilike("%flight_logs%")).first()
    if not doc:
        print("Flight log document not found.")
        return

    pages = db.query(Page).filter(Page.document_id == doc.id).all()
    print(f"Found {len(pages)} pages. Parsing content...")

    # Pattern: LOG_ENTRY YYYY-MM-DD: Tail Number <TAIL>. Passengers: <A>, <B>. Destination: <DEST>
    # Logic in pdf was: "LOG_ENTRY 2002-02-12: Tail Number N212JE. Passengers: Epstein, J., Maxwell, G., Bill Clinton. Destination: Teterboro (TEB) to Paris (LBG)."
    
    pattern = r"LOG_ENTRY (\d{4}-\d{2}-\d{2}): Tail Number ([A-Z0-9]+)\. Passengers: (.*?)\. Destination: (.*?)\."
    
    count = 0
    for p in pages:
        text = p.text_content
        matches = re.findall(pattern, text)
        for date_str, tail, pax, route in matches:
            # Convert date
            try:
                date_val = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue

            # Check duplicate
            existing = db.query(FlightLog).filter(
                FlightLog.date == date_val,
                FlightLog.tail_number == tail
            ).first()
            
            if not existing:
                # Parse route
                origin = ""
                dest = ""
                if " to " in route:
                    parts = route.split(" to ")
                    origin = parts[0].strip()
                    dest = parts[1].strip()
                else:
                    dest = route
                
                log = FlightLog(
                    tail_number=tail,
                    date=date_val,
                    origin=origin,
                    destination=dest,
                    passengers=pax
                )
                db.add(log)
                count += 1
    
    db.commit()
    print(f"Parsed and inserted {count} flight logs.")

if __name__ == "__main__":
    parse_flight_logs()
