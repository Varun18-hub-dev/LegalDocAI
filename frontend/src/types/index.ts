export type DocumentStatus = 'uploading' | 'processing' | 'processed' | 'failed';

export interface UserDocument {
  id: string;
  filename: string;
  file_path: string;
  status: DocumentStatus;
  total_pages: number | null;
  total_chunks: number | null;
  uploaded_at: string;
  metadata: Record<string, any>;
}

export interface ParentNodeInfo {
  node_number: string;
  title: string;
}

export interface OutboundReference {
  citation_text: string;
}

export interface LegalNode {
  id: string;
  document_id: string;
  node_type: string;
  node_number: string;
  title: string;
  text_content: string;
  parent_node_id: string | null;
  index_order: number;
  chroma_id: string | null;
  parents?: ParentNodeInfo[];
  children?: LegalNode[];
  outbound_references?: OutboundReference[];
  confidence_score?: number;
  confidence_category?: 'High' | 'Medium' | 'Low';
  explanation?: {
    original_semantic_rank?: number | null;
    original_keyword_rank?: number | null;
    rrf_score?: number;
    rerank_score?: number | null;
    final_rank?: number;
  };
}

export interface PipelineMetrics {
  intent: string;
  scope: 'global' | 'user_doc';
  retrieved_nodes: number;
  expanded_nodes: number;
  prompt_char_size: number;
  model_used: string;
  tokens_sent: number;
  tokens_received: number;
  timings: Record<string, number>;
  errors: string[];
  processing_time_ms?: number;
}

export interface CitationSchema {
  index: number;
  document_id: string;
  node_id: string | null;
  type: string; // 'statute', 'judgment', 'notification', 'user_document'
  act_name?: string | null;
  coordinate?: string | null;
  title?: string | null;
  case_name?: string | null;
  citation?: string | null;
  segment?: string | null;
  filename?: string | null;
  page?: number | null;
  snippet: string;
  confidence_score?: number;
}

export interface SearchResponse {
  answer: string;
  citations: CitationSchema[];
  metadata: PipelineMetrics;
}

export interface ChatMessage {
  id?: number;
  session_id: string;
  question: string;
  answer: string;
  sources: Array<{
    page: number;
    text: string;
    score?: number;
  }>;
  created_at: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  history: ChatMessage[];
}

export interface ComparisonResponse {
  comparison_summary: string;
  doc_1_title: string;
  doc_2_title: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  sqlite: string;
  chromadb: string;
  gemini: string;
  knowledge_base: string;
  embedding_model: string;
  api_version: string;
}
