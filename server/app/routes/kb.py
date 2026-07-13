from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import QueryRequest, QueryResponse
from app.models.context import QueryContext
from app.services.orchestrator import QueryOrchestrator
from app.utils.logging import get_logger
from app.auth.dependencies import get_current_user

log = get_logger("routes.kb")
router = APIRouter(prefix="/kb", tags=["Knowledge Base"])

@router.post("/query", response_model=QueryResponse)
async def query_global_knowledge_base(payload: QueryRequest, current_user: dict = Depends(get_current_user)):
    """
    Query the global Indian Legal Knowledge Base (Constitution, BNS, BNSS, BSA, Contract, etc.)
    using hybrid vector-database retrieval and Gemini RAG reasoning.
    """
    log.info(f"Received global KB query: '{payload.question}'")
    
    # 1. Create QueryContext
    context = QueryContext(question=payload.question, session_id=payload.session_id)
    
    # 2. Execute pipeline through Orchestrator
    QueryOrchestrator.route(context)
    
    # Check for critical execution errors
    if not context.formatted_answer and context.errors:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {context.errors[0]}")
        
    # Persist to database if session_id is active
    if payload.session_id:
        from app.models.database import get_chat_session, create_chat_session, insert_chat_message
        session = get_chat_session(payload.session_id)
        if not session:
            # Generate a title based on the first 40 characters of the question
            title = payload.question[:40] + ("..." if len(payload.question) > 40 else "")
            create_chat_session(
                session_id=payload.session_id,
                user_id=current_user["id"],
                title=title,
                tags_list=["global"]
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
