"""
Admin Document Upload Endpoint
API for uploading documents through web interface in production
"""
from fastapi import File, UploadFile, HTTPException
from typing import List
import shutil
from pathlib import Path
import PyPDF2
import io

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
    return {
        "total_documents": db.query(models.Document).count(),
        "total_pages": db.query(models.Page).count(),
        "total_entities": db.query(models.Entity).count(),
        "total_relationships": db.query(models.Relationship).count(),
        "datasets": db.query(models.Document.dataset, func.count(models.Document.id)).group_by(models.Document.dataset).all()
    }
