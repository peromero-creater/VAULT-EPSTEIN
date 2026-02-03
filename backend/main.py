from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import crud, models, database, search
from typing import List, Optional

app = FastAPI(title="DOJ Document Explorer API")

database.init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "DOJ Document Explorer API is running"}

@app.get("/countries")
async def read_countries(db: Session = Depends(database.get_db)):
    return crud.get_countries(db)

@app.get("/country/{country_code}")
async def read_country(country_code: str, db: Session = Depends(database.get_db)):
    country = crud.get_country_details(db, country_code)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country

@app.get("/person/{name}")
async def read_person(name: str, db: Session = Depends(database.get_db)):
    person = crud.get_person_details(db, name)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

@app.get("/page/{page_id}")
async def read_page(page_id: int, db: Session = Depends(database.get_db)):
    page = crud.get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

@app.get("/search")
async def search(q: str, country: Optional[str] = None):
    filters = {}
    if country:
        filters["countries"] = [country]
    results = search.search_pages(q, filters=filters)
    return results
