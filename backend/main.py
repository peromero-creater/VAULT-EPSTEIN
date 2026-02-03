from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
import crud, models, database
import search as search_module
from typing import List, Optional
import PyPDF2
import io
from ai_service import get_ai_service
import os
from fastapi.responses import FileResponse, RedirectResponse
import countries_data
from dotenv import load_dotenv

load_dotenv()

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
    person = crud.get_person_details_enhanced(db, name)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

@app.get("/flights")
async def read_flights(limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.get_flights(db, limit=limit)

@app.get("/narratives")
async def read_narratives(type: Optional[str] = None, db: Session = Depends(database.get_db)):
    return crud.get_narratives(db, narrative_type=type)

@app.get("/drive")
async def read_drive(db: Session = Depends(database.get_db)):
    # Mimics JDrive: List documents
    return db.query(models.Document).limit(100).all()


@app.get("/photos")
async def read_photos(db: Session = Depends(database.get_db)):
    # Mimics JPhotos: List document images
    return db.query(models.Document).filter(models.Document.doc_type == "IMAGE").limit(100).all()

@app.get("/page/{page_id}")

async def read_page(page_id: int, db: Session = Depends(database.get_db)):
    page = crud.get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

@app.get("/search")
async def search(q: str, country: Optional[str] = None, db: Session = Depends(database.get_db)):
    filters = {}
    if country:
        filters["countries"] = [country]
    results = search_module.search_pages(q, db=db, filters=filters)
    for hit in results:
        source = hit.get("_source", {})
        doc_id = source.get("document_id")
        if doc_id:
            doc = db.get(models.Document, doc_id)
            hit["external_url"] = doc.external_url if doc else None
            hit["dataset"] = doc.dataset if doc else "GENERAL"
        else:
            hit["external_url"] = None
            hit["dataset"] = "GENERAL"
        
        # New: Extract related entities for this page
        page_id = source.get("page_id")
        if page_id:
            entities = db.query(models.Entity).join(models.PageEntity).filter(models.PageEntity.page_id == page_id).all()
            hit["entities"] = [{"name": e.name, "type": e.type, "id": e.id} for e in entities]
        else:
             hit["entities"] = []
    return results

@app.post("/upload")
async def upload_file(db: Session = Depends(database.get_db)):
    # Mock upload record creation to demonstrate database power
    new_doc = models.Document(
        filename="INTERNAL_RELEASE_2024.pdf",
        path="local/vault/upload",
        doc_type="PDF"
    )
    db.add(new_doc)
    db.flush()
    
    # Mock a couple of declassified pages
    mock_texts = [
        "TRANSCRIPT_STUB: Investigation into financial structures of offshore entities. High relevance to the 2019 inquiry.",
        "LOGS_EXTRACT: Departure from Teterboro at 14:00. Destination: Zorro Ranch. Three passengers listed under pseudonyms.",
        "DEPOSITION_EXTRACT: Witness details accounts of events at the Manhattan townhouse. Further verification required."
    ]
    
    for i, txt in enumerate(mock_texts):
        p = models.Page(
            document_id=new_doc.id,
            page_num=i+1,
            text_content=txt,
            media_type="page_image"
        )
        db.add(p)
    
    db.commit()
    return {"message": "Document successfully ingested into the vault", "doc_id": new_doc.id}

@app.get("/connections")
async def get_connections(db: Session = Depends(database.get_db)):
    rels = db.query(models.Relationship).all()
    output = []
    for r in rels:
        source = db.get(models.Entity, r.source_entity_id)
        target = db.get(models.Entity, r.target_entity_id)
        output.append({
            "id": r.id,
            "source": source.name if source else "Unknown",
            "target": target.name if target else "Unknown",
            "type": r.rel_type,
            "description": r.description
        })
    return output

@app.get("/countries-stats")
async def get_countries_stats(db: Session = Depends(database.get_db)):
    stats = db.query(models.CountryStats).all()
    results = []
    for s in stats:
        # Get top entities for this country
        entities = db.query(models.Entity.name).filter(models.Entity.country_code == s.country_code).limit(3).all()
        results.append({
            "country_code": s.country_code,
            "doc_count": s.doc_count,
            "page_count": s.page_count,
            "top_entities": [e.name for e in entities]
        })
    return results

@app.get("/narrative/{entity_id}")
async def get_narrative(entity_id: int, db: Session = Depends(database.get_db)):
    entity = db.get(models.Entity, entity_id)
    if not entity:
        return {"narrative": "Subject not found in the vault."}
    
    # Simple story generator based on connections
    rels = db.query(models.Relationship).filter(
        (models.Relationship.source_entity_id == entity_id) | 
        (models.Relationship.target_entity_id == entity_id)
    ).all()
    
    if not rels:
        return {"narrative": f"Intelligence reports show {entity.name} is present in the archive, but no direct verified links to other high-profile targets have been established yet."}
    
    # Construct a story
    targets = []
    for r in rels:
        other_id = r.target_entity_id if r.source_entity_id == entity_id else r.source_entity_id
        other = db.get(models.Entity, other_id)
        if other:
            targets.append(f"{other.name} ({r.rel_type})")
    
    story = f"THE STORY SO FAR: Intelligence mapping reveals {entity.name} as a central node in the network. "
    story += f"Records show confirmed links to {', '.join(targets)}. "
    story += "Evidence suggests a complex web of shared flights and co-conspiracies spanning decades, with significant activity centered around the US Virgin Islands and New York."
    
    return {"narrative": story}

@app.get("/search-narrative")
async def get_search_narrative(q: str, db: Session = Depends(database.get_db)):
    # Try to find a PERSON in the query
    entity = db.query(models.Entity).filter(models.Entity.name.ilike(f"%{q}%"), models.Entity.type == "PERSON").first()
    if entity:
        return await get_narrative(entity.id, db)
    
    # Use AI to generate narrative if available
    ai = get_ai_service()
    if ai.is_available():
        # Get some relevant documents
        results = search_module.search_pages(q, db=db, limit=3)
        if results:
            entities = [q]
            context = " ".join([r.get("_source", {}).get("text", "")[:200] for r in results])
            narrative = ai.generate_narrative(entities, context)
            return {"narrative": narrative}
    
    return {"narrative": f"Parsing archives for '{q}'... Preliminary analysis shows scattered references, but no solidified narrative structure has emerged yet. Continue scanning for deeper connections."}

# AI-Powered Endpoints

@app.post("/api/analyze-document/{doc_id}")
async def analyze_document(doc_id: int, db: Session = Depends(database.get_db)):
    """Analyze a document with AI to extract entities and relationships"""
    ai = get_ai_service()
    if not ai.is_available():
        raise HTTPException(status_code=503, detail="AI service not configured. Please set API keys.")
    
    # Get document
    doc = db.get(models.Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get first few pages of text
    pages = db.query(models.Page).filter(models.Page.document_id == doc_id).limit(5).all()
    text = " ".join([p.text_content for p in pages if p.text_content])[:4000]
    
    if not text:
        return {"error": "No text content available for analysis"}
    
    # Analyze with AI
    analysis = ai.analyze_document(text)
    
    # Store AI analysis summary
    doc.ai_analyzed = True
    doc.ai_summary = analysis.get('summary', '')
    
    # Persist Entities and Relationships
    try:
        # 1. Upsert Entities
        name_to_id = {}
        
        # Combine all entities
        all_entities = []
        for p in analysis.get('people', []):
             all_entities.append({"name": p, "type": "PERSON"})
        for o in analysis.get('organizations', []):
             all_entities.append({"name": o, "type": "ORG"})
        for l in analysis.get('locations', []):
             all_entities.append({"name": l, "type": "LOC"})
             
        for ent_data in all_entities:
            # Check if exists
            existing = db.query(models.Entity).filter(
                models.Entity.name == ent_data['name'], 
                models.Entity.type == ent_data['type']
            ).first()
            
            if existing:
                name_to_id[ent_data['name']] = existing.id
            else:
                new_ent = models.Entity(name=ent_data['name'], type=ent_data['type'])
                db.add(new_ent)
                db.flush()
                name_to_id[ent_data['name']] = new_ent.id
                
            # Link to Page (first page of doc for now, or we could be more specific)
            if pages:
                page_id = pages[0].id
                # Check if PageEntity exists
                pe = db.query(models.PageEntity).filter(
                    models.PageEntity.page_id == page_id,
                    models.PageEntity.entity_id == name_to_id[ent_data['name']]
                ).first()
                if not pe:
                    new_pe = models.PageEntity(page_id=page_id, entity_id=name_to_id[ent_data['name']])
                    db.add(new_pe)

        # 2. Insert Relationships
        for rel in analysis.get('relationships', []):
            source_name = rel.get('source')
            target_name = rel.get('target')
            
            if source_name in name_to_id and target_name in name_to_id:
                # Check for duplicate relationship
                exists = db.query(models.Relationship).filter(
                    models.Relationship.source_entity_id == name_to_id[source_name],
                    models.Relationship.target_entity_id == name_to_id[target_name],
                    models.Relationship.rel_type == rel.get('type')
                ).first()
                
                if not exists:
                    new_rel = models.Relationship(
                        source_entity_id=name_to_id[source_name],
                        target_entity_id=name_to_id[target_name],
                        rel_type=rel.get('type'),
                        description=rel.get('description'),
                        confidence_score=0.8 # AI generated
                    )
                    db.add(new_rel)

    except Exception as e:
        print(f"Error persisting AI analysis: {e}")
        # Don't fail the whole request, just log
    
    db.commit()
    
    return analysis

@app.get("/api/document-narrative/{doc_id}")
async def get_document_narrative(doc_id: int, db: Session = Depends(database.get_db)):
    """Get AI-generated narrative for a document"""
    doc = db.get(models.Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Return cached summary if available
    if doc.ai_summary:
        return {"narrative": doc.ai_summary}
    
    # Generate new analysis
    result = await analyze_document(doc_id, db)
    return {"narrative": result.get('summary', 'No summary available')}

@app.post("/api/discover-connections/{entity_name}")
async def discover_connections(entity_name: str, db: Session = Depends(database.get_db)):
    """Use AI to discover connections for an entity"""
    ai = get_ai_service()
    if not ai.is_available():
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    # Search for documents mentioning this entity
    results = search_module.search_pages(entity_name, db=db, limit=10)
    
    if not results:
        return {"connections": [], "message": "No documents found"}
    
    # Extract document snippets
    snippets = [r.get("_source", {}).get("text", "") for r in results]
    
    # Use AI to find connections
    connections = ai.find_connections(entity_name, snippets)
    
    return {"entity": entity_name, "connections": connections}

@app.get("/api/country-summary/{country_code}")
async def get_country_summary(country_code: str, db: Session = Depends(database.get_db)):
    """Get AI-generated summary for a country's intelligence"""
    ai = get_ai_service()
    
    country_info = countries_data.get_country_info(country_code)
    
    # Get documents related to this country
    entities = db.query(models.Entity).filter(models.Entity.country_code == country_code).all()
    
    if not entities:
        return {"summary": f"No intelligence available for {country_info.get('name', country_code)}", "country": country_info}
    
    # Get pages mentioning this country
    entity_ids = [e.id for e in entities]
    pages = db.query(models.Page).join(models.PageEntity).filter(
        models.PageEntity.entity_id.in_(entity_ids)
    ).limit(5).all()
    
    documents = [{"text": p.text_content} for p in pages if p.text_content]
    
    if ai.is_available() and documents:
        summary = ai.summarize_country_intel(country_code, documents)
    else:
        summary = f"Found {len(entities)} entities and {len(pages)} pages related to {country_info.get('name', country_code)}"
    
    return {
        "country_code": country_code,
        "country_name": country_info.get('name', country_code),
        "summary": summary,
        "entity_count": len(entities),
        "page_count": len(pages)
    }

@app.get("/api/countries-search")
async def search_countries(q: str = ""):
    """Search countries by name or code"""
    if q:
        return countries_data.search_countries(q)
    return [{"code": code, **info} for code, info in countries_data.COUNTRY_DATA.items()]

@app.get("/api/suggestions")
async def get_suggestions(q: str, db: Session = Depends(database.get_db)):
    """Get search suggestions based on query"""
    if len(q) < 2:
        return []
    
    # Search documents titles
    docs = db.query(models.Document.filename).filter(models.Document.filename.ilike(f"%{q}%")).limit(3).all()
    doc_titles = [d.filename for d in docs]
    
    # Search entities
    entities = db.query(models.Entity.name).filter(models.Entity.name.ilike(f"%{q}%")).limit(5).all()
    entity_names = [e.name for e in entities]
    
    return list(set(doc_titles + entity_names))

@app.get("/document/{doc_id}")
async def get_document(doc_id: int, db: Session = Depends(database.get_db)):
    """Get document metadata"""
    doc = db.get(models.Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@app.get("/documents/{doc_id}/raw")
async def get_document_raw(doc_id: int, db: Session = Depends(database.get_db)):
    """Serve the raw PDF file for a document"""
    doc = db.get(models.Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 0. Check for S3 Path
    if doc.path.startswith("s3://"):
        from backend.storage import storage
        presigned = storage.get_presigned_url(doc.path)
        if presigned:
            return RedirectResponse(url=presigned)
        else:
             raise HTTPException(status_code=500, detail="Could not generate cloud link")

    # 1. Determine Project Root (parent of backend/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # 2. Heuristic Path Resolution
    possible_paths = []
    
    # Raw path from DB
    possible_paths.append(doc.path)
    
    # Relative to project root (e.g. data/files/foo.pdf)
    possible_paths.append(os.path.join(project_root, doc.path))
    
    # Relative to backend (unlikely but possible)
    possible_paths.append(os.path.join(current_dir, doc.path))
    
    # Hardcoded data/files check if path is just filename
    if "/" not in doc.path and "\\" not in doc.path:
        possible_paths.append(os.path.join(project_root, "data", "files", doc.path))

    final_path = None
    for p in possible_paths:
        # Normalize path separators
        p = p.replace("/", os.sep).replace("\\", os.sep)
        print(f"Checking path: {p}") # DEBUG
        if os.path.exists(p) and os.path.isfile(p):
            final_path = p
            print(f"Found file at: {final_path}") # DEBUG
            break
            
    if not final_path:
        # Special case for JMail or URLs stored in path
        if "jmail" in doc.path.lower() or "http" in doc.path:
             # We can't serve a file, but we shouldn't crash. 
             # For now, return 404 but with specific detail
             raise HTTPException(status_code=404, detail=f"Document appears to be external/missing: {doc.path}")
             
        raise HTTPException(status_code=404, detail=f"File not found on server at {doc.path}")
        
    headers = {
        "Content-Disposition": f"inline; filename={doc.filename}",
        "Content-Type": "application/pdf"
    }
    return FileResponse(final_path, media_type="application/pdf", filename=doc.filename, headers=headers)

@app.get("/document/{doc_id}/pages")
async def get_document_pages(doc_id: int, db: Session = Depends(database.get_db)):
    """Get all pages for a document"""
    pages = db.query(models.Page).filter(models.Page.document_id == doc_id).all()
    return pages

# Admin Upload Endpoints for Production

@app.post("/admin/upload-documents")
async def upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(database.get_db)
):
    """
    Upload documents via web interface
    For production use with admin authentication
    """
    uploaded = []
    errors = []
    
    for file in files:
        try:
            # Validate file type
            if not file.filename.endswith('.pdf'):
                errors.append(f"{file.filename}: Only PDF files allowed")
                continue
            
            # Read file content
            content = await file.read()
            
            # Check if already exists
            existing = db.query(models.Document).filter(
                models.Document.filename == file.filename
            ).first()
            
            if existing:
                errors.append(f"{file.filename}: Already exists")
                continue
            
            # Create document record
            document = models.Document(
                filename=file.filename,
                path=f"/uploads/{file.filename}",
                external_url=None,
                doc_type="PDF",
                dataset="User-Upload"
            )
            db.add(document)
            db.flush()
            
            # Extract text from PDF
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                pages_extracted = 0
                
                for page_num, pdf_page in enumerate(pdf_reader.pages, 1):
                    try:
                        text = pdf_page.extract_text()
                        if text and text.strip():
                            page = models.Page(
                                document_id=document.id,
                                page_num=page_num,
                                text_content=text[:10000],
                                text_quality=0.7,
                                media_type='pdf_page'
                            )
                            db.add(page)
                            pages_extracted += 1
                    except:
                        continue
                
                db.commit()
                uploaded.append({
                    "filename": file.filename,
                    "pages": pages_extracted,
                    "document_id": document.id
                })
                
            except Exception as e:
                db.rollback()
                errors.append(f"{file.filename}: {str(e)}")
                
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    return {
        "uploaded": uploaded,
        "errors": errors,
        "success_count": len(uploaded),
        "error_count": len(errors)
    }

@app.get("/admin/document-stats")
async def get_document_stats(db: Session = Depends(database.get_db)):
    """Get database statistics"""
    datasets = db.query(models.Document.dataset, func.count(models.Document.id)).group_by(models.Document.dataset).all()
    return {
        "total_documents": db.query(models.Document).count(),
        "total_pages": db.query(models.Page).count(),
        "total_entities": db.query(models.Entity).count(),
        "total_relationships": db.query(models.Relationship).count(),
        "datasets": [{"name": d[0] or "Unknown", "count": d[1]} for d in datasets]
    }
