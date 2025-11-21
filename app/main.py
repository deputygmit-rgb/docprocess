from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from app.core.config import get_settings
from app.core.database import get_db, engine
from app.models.document import Base, Document, ProcessingStatus
from app.services.celery_app import process_document_task
from app.services.vision_service import VisionService

settings = get_settings()

Base.metadata.create_all(bind=engine)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Document processing API with graph-based layout extraction"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Document Processor API",
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/extract-layout")
async def extract_layout(request: dict):
    """Extract layout and chart details from an image.
    
    Request body:
    {
        "image": "data:image/jpeg;base64,..." or "data:image/png;base64,..."
    }
    """
    try:
        image_data = request.get("image")
        if not image_data:
            raise HTTPException(status_code=400, detail="No image provided")
        
        vision_service = VisionService()
        result = vision_service.extract_layout(image_data, page_number=1)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Layout extraction failed: {str(e)}")


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is empty")
    
    allowed_extensions = {'.pdf', '.docx', '.pptx', '.xlsx', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.doc', '.odt', '.ppt', '.odp', '.xls', '.ods'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(sorted(allowed_extensions))}"
        )
    
    file_path = os.path.join(settings.UPLOAD_DIR, f"{datetime.utcnow().timestamp()}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        
        if file_size > settings.MAX_FILE_SIZE:
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        doc = Document(
            filename=file.filename,
            file_type=file_ext,
            file_path=file_path,
            file_size=file_size,
            status=ProcessingStatus.PENDING
        )
        
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Run task synchronously
        result = process_document_task.apply_async((doc.id,))
        result.get(timeout=30)  # Wait for result
        
        # Refresh document to get updated status
        db.refresh(doc)
        
        return {
            "document_id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "status": doc.status,
            "error_message": doc.error_message,
            "message": "Document processed successfully" if doc.status == ProcessingStatus.COMPLETED else f"Document processing {doc.status}"
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 10,
    status: Optional[ProcessingStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Document)
    
    if status:
        query = query.filter(Document.status == status)
    
    total = query.count()
    documents = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "status": doc.status,
                "created_at": doc.created_at.isoformat(),
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None
            }
            for doc in documents
        ]
    }


@app.get("/documents/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat(),
        "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
        "error_message": doc.error_message,
        "layout_data": doc.layout_data,
        "graph_data": doc.graph_data,
        "processed_json": doc.processed_json
    }


@app.delete("/documents/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    db.delete(doc)
    db.commit()
    
    return {"message": "Document deleted successfully", "document_id": document_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
