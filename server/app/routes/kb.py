from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse
from app.models.context import QueryContext
from app.services.orchestrator import QueryOrchestrator
from app.utils.logging import get_logger

log = get_logger("routes.kb")
router = APIRouter(prefix="/kb", tags=["Knowledge Base"])

@router.post("/query", response_model=QueryResponse)
async def query_global_knowledge_base(payload: QueryRequest):
    """
    Query the global Indian Legal Knowledge Base (Constitution, BNS, BNSS, BSA, Contract, etc.)
    using hybrid vector-database retrieval and Gemini RAG reasoning.
    """
    log.info(f"Received global KB query: '{payload.question}'")
    
    # 1. Create QueryContext
    context = QueryContext(question=payload.question)
    
    # 2. Execute pipeline through Orchestrator
    QueryOrchestrator.route(context)
    
    # Check for critical execution errors
    if not context.formatted_answer and context.errors:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {context.errors[0]}")
        
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
