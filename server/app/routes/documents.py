import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Query, Depends
from app.models.schemas import UploadResponse, StatusResponse, QueryRequest, QueryResponse, SummaryResponse, ComparisonRequest, ComparisonResponse, MessageResponse
from app.models.database import insert_user_document, get_user_document, delete_user_document_db, insert_chat_log
from app.models.context import QueryContext, Intent
from app.services.pdf_processor import PDFProcessor
from app.services.orchestrator import QueryOrchestrator
from app.utils.logging import get_logger
from app.utils.validators import validate_pdf_file
from app.utils.helpers import generate_unique_id
from scripts.vector_store import get_vector_store
from app.auth.dependencies import get_current_user

log = get_logger("routes.documents")
router = APIRouter(prefix="/documents", tags=["User Documents"])

from app.config import UPLOAD_DIR

@router.post("/upload", response_model=UploadResponse)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    Upload a user contract/legal PDF. Starts background processing
    and returns a unique document ID immediately.
    """
    validate_pdf_file(file.filename)
    doc_id = generate_unique_id("udoc")
    file_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"
    
    log.info(f"Uploading file {file.filename} -> saving to {file_path}")
    
    # Save file stream to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 1. Insert placeholder in SQLite database
    insert_user_document(
        doc_id=doc_id,
        filename=file.filename,
        file_path=str(file_path),
        status="uploading",
        user_id=current_user["id"],
        owner_name=current_user["name"],
        visibility="PRIVATE",
        created_by=current_user["name"]
    )
    
    # 2. Trigger asynchronous background parsing and embedding task
    background_tasks.add_task(
        PDFProcessor.process,
        doc_id,
        str(file_path),
        file.filename
    )
    
    return UploadResponse(
        document_id=doc_id,
        filename=file.filename,
        status="uploading",
        message="Document uploaded successfully. Processing started in the background."
    )

@router.get("", response_model=list[StatusResponse])
async def list_documents(current_user: dict = Depends(get_current_user)):
    """Retrieve all uploaded user documents."""
    from app.models.database import get_all_user_documents
    docs = get_all_user_documents(user_id=current_user["id"])
    return [
        StatusResponse(
            document_id=doc["id"],
            filename=doc["filename"],
            status=doc["status"],
            total_pages=doc.get("total_pages"),
            total_chunks=doc.get("total_chunks"),
            uploaded_at=doc["uploaded_at"]
        ) for doc in docs
    ]

@router.get("/{doc_id}/status", response_model=StatusResponse)
async def get_document_status(doc_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve the parsing, chunking, and embedding status of an uploaded PDF."""
    doc = get_user_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    # User isolation check
    if doc.get("user_id") != current_user["id"] and doc.get("visibility") != "PUBLIC":
        raise HTTPException(status_code=403, detail="Permission denied. You do not own this document.")
        
    return StatusResponse(
        document_id=doc["id"],
        filename=doc["filename"],
        status=doc["status"],
        total_pages=doc.get("total_pages"),
        total_chunks=doc.get("total_chunks"),
        uploaded_at=doc["uploaded_at"]
    )

@router.post("/{doc_id}/query", response_model=QueryResponse)
async def query_document(doc_id: str, payload: QueryRequest, current_user: dict = Depends(get_current_user)):
    """Ask natural language questions about a specific uploaded document (page cited RAG)."""
    doc = get_user_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    # User isolation check
    if doc.get("user_id") != current_user["id"] and doc.get("visibility") != "PUBLIC":
        raise HTTPException(status_code=403, detail="Permission denied. You do not own this document.")
        
    if doc["status"] != "processed":
        raise HTTPException(status_code=400, detail=f"Document is not ready for query. Current status: {doc['status']}")
        
    log.info(f"Querying document {doc_id} ('{doc['filename']}'): '{payload.question}'")
    
    # Create Context with document scope
    context = QueryContext(question=payload.question, session_id=payload.session_id, document_id=doc_id)
    
    # Execute Pipeline
    QueryOrchestrator.route(context)
    
    if not context.formatted_answer and context.errors:
        raise HTTPException(status_code=500, detail=f"Query failed: {context.errors[0]}")
        
    # Optional: Persist to chat logs if session_id is provided
    if payload.session_id:
        from app.models.database import get_chat_session, create_chat_session, insert_chat_message
        session = get_chat_session(payload.session_id)
        if not session:
            create_chat_session(
                session_id=payload.session_id,
                user_id=current_user["id"],
                title=f"Doc QA: {doc['filename']}",
                tags_list=[f"doc_{doc_id}"]
            )
        # 1. Insert User Query
        insert_chat_message(payload.session_id, "user", payload.question)
        
        # 2. Insert Assistant Answer
        citations_mapped = []
        for c in context.citations:
            try:
                citations_mapped.append(c.dict() if hasattr(c, "dict") else dict(c))
            except Exception:
                citations_mapped.append(dict(c))
        insert_chat_message(payload.session_id, "assistant", context.formatted_answer or "", citations_mapped)
        
    return QueryResponse(
        answer=context.formatted_answer or "",
        citations=context.citations,
        metadata={
            "intent": context.intent.value,
            "retrieved_nodes": len(context.retrieved_nodes),
            "expanded_nodes": len(context.expanded_nodes),
            "llm_model": context.metadata.get("llm_model", "mock"),
            "processing_time_ms": context.timings.get("total_request", 0.0),
            "timings": context.timings,
            "errors": context.errors
        }
    )

@router.get("/{doc_id}/summary", response_model=SummaryResponse)
async def summarize_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    """Generate a structured summary of the uploaded document (Map-Reduce)."""
    doc = get_user_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    # User isolation check
    if doc.get("user_id") != current_user["id"] and doc.get("visibility") != "PUBLIC":
        raise HTTPException(status_code=403, detail="Permission denied. You do not own this document.")
        
    if doc["status"] != "processed":
        raise HTTPException(status_code=400, detail=f"Document is not ready for summary. Current status: {doc['status']}")
        
    log.info(f"Generating summary for document {doc_id}")
    
    # Create context with document summary intent
    context = QueryContext(question="Summarize this document.", document_id=doc_id)
    context.intent = Intent.DOCUMENT_SUMMARY
    
    # Run Orchestrator (which routes to SummaryService)
    QueryOrchestrator.route(context)
    
    if not context.llm_response and context.errors:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {context.errors[0]}")
        
    return SummaryResponse(
        document_id=doc_id,
        summary=context.llm_response or "",
        metadata={
            "processing_time_ms": context.timings.get("total_request", 0.0),
            "timings": context.timings,
            "errors": context.errors
        }
    )

@router.post("/compare", response_model=ComparisonResponse)
async def compare_documents(payload: ComparisonRequest, current_user: dict = Depends(get_current_user)):
    """Compare two uploaded contracts page-by-page and identify changes/differences."""
    doc_1 = get_user_document(payload.doc_id_1)
    doc_2 = get_user_document(payload.doc_id_2)
    
    if not doc_1 or not doc_2:
        raise HTTPException(status_code=404, detail="One or both documents were not found.")
        
    # User isolation check on both documents
    for doc in [doc_1, doc_2]:
        if doc.get("user_id") != current_user["id"] and doc.get("visibility") != "PUBLIC":
            raise HTTPException(status_code=403, detail="Permission denied. You must own both documents to compare them.")
            
    if doc_1["status"] != "processed" or doc_2["status"] != "processed":
        raise HTTPException(status_code=400, detail="Both documents must be processed before comparison.")
        
    log.info(f"Comparing document {payload.doc_id_1} vs {payload.doc_id_2}")
    
    # Create context with comparison metadata
    context = QueryContext(question="Compare these two documents.", document_id=payload.doc_id_1)
    context.intent = Intent.DOCUMENT_COMPARISON
    context.metadata["doc_id_1"] = payload.doc_id_1
    context.metadata["doc_id_2"] = payload.doc_id_2
    
    # Run Orchestrator (routes to ComparisonService)
    QueryOrchestrator.route(context)
    
    if not context.llm_response and context.errors:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {context.errors[0]}")
        
    return ComparisonResponse(
        comparison_summary=context.llm_response or "",
        metadata={
            "processing_time_ms": context.timings.get("total_request", 0.0),
            "timings": context.timings,
            "errors": context.errors
        }
    )

@router.delete("/{doc_id}", response_model=MessageResponse)
async def delete_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    """Delete the document record from SQLite, erase the uploaded file, and clear vectors from ChromaDB."""
    doc = get_user_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    # User isolation check
    if doc.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Permission denied. You can only delete your own documents.")
        
    log.info(f"Deleting document {doc_id} ('{doc['filename']}')")
    
    # 1. Delete vectors from ChromaDB
    try:
        store = get_vector_store()
        collection = store.get_or_create_collection(name="case_documents")
        collection.delete(where={"law": doc_id})
        log.info("Cleared vectors from ChromaDB.")
    except Exception as e:
        log.warning(f"ChromaDB vector delete failed (may have no vectors): {e}")
        
    # 2. Delete local file
    file_path = doc["file_path"]
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            log.info(f"Removed local file at: {file_path}")
        except Exception as e:
            log.warning(f"Failed to remove local file: {e}")
            
    # 3. Delete from SQLite database
    delete_user_document_db(doc_id)
    
    return MessageResponse(
        status="success",
        message="Document, local file, and associated vector indices deleted successfully."
    )

@router.get("/{doc_id}/pdf")
async def get_document_pdf(doc_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve the raw PDF file binary stream for frontend rendering."""
    from fastapi.responses import FileResponse
    doc = get_user_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    # User isolation check
    if doc.get("user_id") != current_user["id"] and doc.get("visibility") != "PUBLIC":
        raise HTTPException(status_code=403, detail="Permission denied. You do not own this document.")
        
    file_path = doc["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk.")
    return FileResponse(file_path, media_type="application/pdf", filename=doc["filename"])
