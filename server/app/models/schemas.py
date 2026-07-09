from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    question: str = Field(..., description="The query question string.")
    session_id: Optional[str] = Field(None, description="Optional chat session identifier for persistence.")

class CitationSchema(BaseModel):
    index: int
    document_id: str
    node_id: Optional[str]
    type: str  # 'statute', 'judgment', 'notification', 'user_document'
    act_name: Optional[str] = None
    coordinate: Optional[str] = None
    title: Optional[str] = None
    case_name: Optional[str] = None
    citation: Optional[str] = None
    segment: Optional[str] = None
    filename: Optional[str] = None
    page: Optional[int] = None
    snippet: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[CitationSchema]
    metadata: Dict[str, Any]

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str

class StatusResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    total_pages: Optional[int] = None
    total_chunks: Optional[int] = None
    uploaded_at: str

class SummaryResponse(BaseModel):
    document_id: str
    summary: str
    metadata: Dict[str, Any]

class ComparisonRequest(BaseModel):
    doc_id_1: str
    doc_id_2: str

class ComparisonResponse(BaseModel):
    comparison_summary: str
    metadata: Dict[str, Any]

class ChatLogSchema(BaseModel):
    id: int
    session_id: str
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    created_at: str

class ChatHistoryResponse(BaseModel):
    session_id: str
    history: List[ChatLogSchema]

class MessageResponse(BaseModel):
    status: str
    message: str

class HealthResponse(BaseModel):
    status: str
    environment: str
    sqlite: str
    chromadb: str
    uploads: str
    gemini: str
    kb_version: str

class UserRegisterRequest(BaseModel):
    name: str = Field(..., description="User's display name.")
    email: str = Field(..., description="User's email address.")
    password: str = Field(..., description="User's raw password.")
    role: str = Field("USER", description="User's access role (ADMIN, USER).")

class UserLoginRequest(BaseModel):
    email: str = Field(..., description="User's email address.")
    password: str = Field(..., description="User's raw password.")

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

