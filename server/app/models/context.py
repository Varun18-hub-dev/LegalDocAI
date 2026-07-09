import time
from enum import Enum
from typing import List, Dict, Any, Optional

class Intent(str, Enum):
    EXPLAIN_LAW = "EXPLAIN_LAW"
    CASE_SEARCH = "CASE_SEARCH"
    LEGAL_RESEARCH = "LEGAL_RESEARCH"
    DOCUMENT_QA = "DOCUMENT_QA"
    DOCUMENT_SUMMARY = "DOCUMENT_SUMMARY"
    DOCUMENT_COMPARISON = "DOCUMENT_COMPARISON"
    GENERAL_CHAT = "GENERAL_CHAT"
    UNKNOWN = "UNKNOWN"

class QueryContext:
    """
    Shared context object carrying request state, timings, retrieved content,
    and formatted responses through the services pipeline.
    """
    def __init__(self, question: str, session_id: Optional[str] = None, document_id: Optional[str] = None):
        self.question: str = question
        self.session_id: Optional[str] = session_id
        self.document_id: Optional[str] = document_id
        
        # State variables
        self.intent: Intent = Intent.UNKNOWN
        self.scope: str = "global" if not document_id else "user_doc"
        self.user_id: Optional[str] = None
        
        # Pipelines data
        self.retrieved_nodes: List[Dict[str, Any]] = []
        self.expanded_nodes: List[Dict[str, Any]] = []
        self.prompt: Optional[str] = None
        self.llm_response: Optional[str] = None
        self.citations: List[Dict[str, Any]] = []
        self.formatted_answer: Optional[str] = None
        
        # Metrics and diagnostics
        self.metadata: Dict[str, Any] = {}
        self.timings: Dict[str, float] = {}
        self.errors: List[str] = []
        
        # Helper for timing
        self._start_times: Dict[str, float] = {}

    def start_stage(self, stage_name: str) -> None:
        """Start measuring execution time for a pipeline stage."""
        self._start_times[stage_name] = time.time()

    def end_stage(self, stage_name: str) -> None:
        """End measuring execution time and store duration in milliseconds."""
        if stage_name in self._start_times:
            duration = (time.time() - self._start_times[stage_name]) * 1000
            self.timings[stage_name] = round(duration, 2)
            del self._start_times[stage_name]
