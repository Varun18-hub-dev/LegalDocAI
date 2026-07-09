import time
from typing import Dict, Any
from app.models.context import QueryContext, Intent
from app.services.retriever import Retriever
from app.services.reference_service import ReferenceService
from app.services.prompt_builder import PromptBuilder
from app.services.llm_service import LLMService
from app.services.citation_formatter import CitationFormatter
from app.services.summary_service import SummaryService
from app.services.comparison_service import ComparisonService
from app.utils.logging import get_logger

log = get_logger("orchestrator")

class QueryOrchestrator:
    """
    Central decision and coordination engine. Classifies intent,
    routes requests to retrievers, prompts, LLMs, and formats final responses.
    """
    
    @staticmethod
    def route(context: QueryContext) -> QueryContext:
        """
        Public contract method that orchestrates the query lifecycle from request to response.
        Tracks performance metrics and timings.
        """
        start_time = time.time()
        context.start_stage("total_request")
        
        try:
            log.info(f"Incoming query: '{context.question}'")
            
            # Step 1: Detect User Intent
            QueryOrchestrator._detect_intent(context)
            
            # Step 2: Route to specialized pipelines
            if context.intent == Intent.DOCUMENT_SUMMARY:
                # Document Summary Pipeline
                SummaryService.summarize(context)
            elif context.intent == Intent.DOCUMENT_COMPARISON:
                # Document Comparison Pipeline
                ComparisonService.compare(context)
            elif context.intent == Intent.GENERAL_CHAT:
                # General Chat Pipeline (No retrieval required)
                PromptBuilder.build(context)
                LLMService.generate(context)
            else:
                # Standard Search & RAG Pipeline (EXPLAIN_LAW, CASE_SEARCH, LEGAL_RESEARCH, DOCUMENT_QA)
                
                # Retrieval
                Retriever.retrieve(context)
                
                # Never call Gemini with empty context on user document Q&A (Final Requirement)
                if context.intent == Intent.DOCUMENT_QA and not context.retrieved_nodes:
                    context.formatted_answer = "I could not find a matching section in this document. Try asking about rent, deposit, utilities, pets, or lease term."
                    log.info("Document Q&A returned early due to empty context.")
                    return context
                
                # Reference Expansion (Only for global law explanations/research)
                if context.scope == "global" and context.intent in (Intent.EXPLAIN_LAW, Intent.LEGAL_RESEARCH):
                    ReferenceService.expand(context)
                    
                # Prompt Construction
                PromptBuilder.build(context)
                
                # Log final prompt context passed to LLM (Step 6)
                log.info(f"Final Prompt Context passed to LLM (Step 6):\n{context.prompt}")
                
                # LLM Execution
                LLMService.generate(context)
                
            # Step 3: Citation Formatting (Applies to all pipelines that retrieve content)
            if context.intent != Intent.GENERAL_CHAT:
                CitationFormatter.format(context)
            else:
                context.formatted_answer = context.llm_response
                
            # Log retrieval pipeline telemetry
            QueryOrchestrator._log_pipeline_metrics(context, start_time)
            
        except Exception as e:
            log.error(f"Pipeline orchestration failed: {e}", exc_info=True)
            context.errors.append(f"Orchestration error: {str(e)}")
            if not context.llm_response:
                context.formatted_answer = f"Error processing query: {str(e)}"
        finally:
            context.end_stage("total_request")
            
        return context

    @staticmethod
    def _detect_intent(context: QueryContext) -> None:
        """Classify user query intent into an Intent enum."""
        context.start_stage("intent_detection")
        q = context.question.lower()
        
        intent = Intent.UNKNOWN
        
        if context.scope == "user_doc":
            # User document queries
            if any(w in q for w in ("compare", "difference", "versus", "vs", "additions", "removals")):
                intent = Intent.DOCUMENT_COMPARISON
            elif any(w in q for w in ("summarize", "summary", "outline", "executive summary")):
                intent = Intent.DOCUMENT_SUMMARY
            else:
                intent = Intent.DOCUMENT_QA
        else:
            # Global KB queries
            if any(w in q for w in ("hello", "hi ", "hey", "who are you", "thank you", "thanks")):
                intent = Intent.GENERAL_CHAT
            elif any(w in q for w in ("judgment", "court", "bench", "decided", "versus", " v ")):
                intent = Intent.CASE_SEARCH
            elif any(w in q for w in ("article", "section", "rule")) and any(c.isdigit() for c in q):
                intent = Intent.EXPLAIN_LAW
            elif any(w in q for w in ("relationship", "difference between", "compare", "link", "connect")):
                intent = Intent.LEGAL_RESEARCH
            else:
                # Default fallback for global KB
                intent = Intent.LEGAL_RESEARCH
                
        context.intent = intent
        log.info(f"Intent classified as: {intent.value}")
        context.end_stage("intent_detection")

    @staticmethod
    def _log_pipeline_metrics(context: QueryContext, start_time: float) -> None:
        """Log structured performance metrics for observability."""
        total_time_ms = (time.time() - start_time) * 1000
        
        retrieved_count = len(context.retrieved_nodes)
        expanded_count = len(context.expanded_nodes)
        
        log.info(
            f"Pipeline Metrics:\n"
            f"  - Intent: {context.intent.value}\n"
            f"  - Scope: {context.scope}\n"
            f"  - Retrieved Nodes: {retrieved_count}\n"
            f"  - Expanded Nodes: {expanded_count}\n"
            f"  - Prompt Char Size: {len(context.prompt or '')}\n"
            f"  - Model Used: {context.metadata.get('llm_model', 'none')}\n"
            f"  - Tokens Sent/Received: {context.metadata.get('tokens_sent', 0)} / {context.metadata.get('tokens_received', 0)}\n"
            f"  - Timings (ms): {context.timings}\n"
            f"  - Errors: {context.errors}"
        )
