from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class HierarchyNode(BaseModel):
    id: str
    document_id: str
    node_type: str  # 'part', 'chapter', 'section', 'subsection', 'proviso', 'explanation', 'illustration', 'clause'
    node_number: Optional[str] = None  # e.g., 'Section 303'
    title: Optional[str] = None
    text_content: str
    parent_node_id: Optional[str] = None
    index_order: int = 0
    chroma_id: Optional[str] = None

class DocumentVersion(BaseModel):
    node_id: str
    version_label: str  # 'Original', 'Amended', 'Current'
    amended_by: Optional[str] = None
    text_content: str
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None

class CrossReference(BaseModel):
    source_node_id: str
    citation_text: str
    target_node_id: Optional[str] = None
    reference_type: Optional[str] = None  # 'cites_statute', 'relies_upon_case', 'amends'

class LegalDocument(BaseModel):
    id: str
    document_type: str  # 'Central Act', 'Rule', 'Judgment', 'Notification'
    title: str
    short_title: Optional[str] = None
    year: Optional[int] = None
    source_url: Optional[str] = None
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    is_current: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
