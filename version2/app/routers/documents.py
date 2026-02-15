"""Documents router — PDF upload, list, delete with per-user Pinecone namespaces."""

import os
import uuid
import shutil
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from pydantic import BaseModel

from app.services.auth_service import get_current_user_id
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ──────────────── Response Models ────────────────

class DocumentResponse(BaseModel):
    id: str
    filename: str
    pages: int
    chunks: int
    uploaded_at: str


class UploadResponse(BaseModel):
    message: str
    document: DocumentResponse


# ──────────────── Upload ────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    """
    Upload a PDF file for RAG processing.
    
    - Saves the file temporarily
    - Extracts text → chunks → embeddings
    - Upserts vectors to Pinecone under namespace user_{user_id}
    - Stores document metadata in MongoDB
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # Size check (10 MB max for free tier friendliness)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10 MB limit.")
    
    doc_id = str(uuid.uuid4())
    temp_path = os.path.join(UPLOAD_DIR, f"{doc_id}.pdf")
    
    try:
        # Save temp file
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Process through RAG service
        rag_service = request.app.state.rag_service
        result = await rag_service.upload_pdf(
            pdf_path=temp_path,
            user_id=user_id,
            doc_id=doc_id,
            original_filename=file.filename,
        )
        
        # Store metadata in MongoDB
        db_service = request.app.state.db_service
        doc_meta = {
            "_id": doc_id,
            "user_id": user_id,
            "filename": file.filename,
            "pages": result["pages"],
            "chunks": result["chunks"],
            "vectors": result["vectors_uploaded"],
            "namespace": result["namespace"],
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        await db_service.db.documents.insert_one(doc_meta)
        
        logger.info("document_uploaded", doc_id=doc_id, user_id=user_id, filename=file.filename)
        
        return UploadResponse(
            message=f"Successfully processed {file.filename}",
            document=DocumentResponse(
                id=doc_id,
                filename=file.filename,
                pages=result["pages"],
                chunks=result["chunks"],
                uploaded_at=doc_meta["uploaded_at"],
            ),
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("upload_failed", doc_id=doc_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process document.")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ──────────────── List ────────────────

@router.get("")
async def list_documents(
    request: Request,
    user_id: str = Depends(get_current_user_id),
):
    """List all documents uploaded by the current user."""
    db_service = request.app.state.db_service
    
    cursor = db_service.db.documents.find(
        {"user_id": user_id},
        {"_id": 1, "filename": 1, "pages": 1, "chunks": 1, "uploaded_at": 1},
    ).sort("uploaded_at", -1)
    
    docs = []
    async for doc in cursor:
        docs.append({
            "id": doc["_id"],
            "filename": doc["filename"],
            "pages": doc.get("pages", 0),
            "chunks": doc.get("chunks", 0),
            "uploaded_at": doc.get("uploaded_at", ""),
        })
    
    return docs


# ──────────────── Delete ────────────────

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id),
):
    """Delete a document's vectors from Pinecone and metadata from MongoDB."""
    db_service = request.app.state.db_service
    
    # Verify ownership
    doc = await db_service.db.documents.find_one(
        {"_id": doc_id, "user_id": user_id}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    try:
        # Delete vectors from Pinecone
        rag_service = request.app.state.rag_service
        await rag_service.delete_document_vectors(doc_id, user_id)
        
        # Delete metadata from MongoDB
        await db_service.db.documents.delete_one({"_id": doc_id})
        
        logger.info("document_deleted", doc_id=doc_id, user_id=user_id)
        return {"message": "Document deleted successfully."}
    
    except Exception as e:
        logger.error("delete_failed", doc_id=doc_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete document.")


# ──────────────── Download ────────────────

@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    request: Request,
):
    """Download a file from GridFS."""
    from fastapi.responses import Response
    
    db_service = request.app.state.db_service
    
    content = await db_service.get_file(file_id)
    if not content:
        raise HTTPException(status_code=404, detail="File not found")
    
    return Response(content=content, media_type="application/octet-stream")
