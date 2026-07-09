import re
import time
from typing import List, Dict, Any, Optional
from app.models.database import get_db_conn
from app.models.context import QueryContext, Intent
from app.utils.logging import get_logger
from app.utils.exceptions import RetrievalError
from scripts.embedding_service import get_embedding_service
from scripts.vector_store import get_vector_store

log = get_logger("retriever")

# =====================================================================
# Module 1 — Query Normalizer
# =====================================================================
class QueryNormalizer:
    """Preprocesses natural legal queries into normalized retrieval search strings."""
    @staticmethod
    def normalize(query: str) -> str:
        if not query:
            return ""
        normalized = query.lower().strip()
        
        # Remove common conversational fillers and helper prefixes
        fillers = [
            r"\bcan\s+you\s+(?:tell|explain|show|give|find|help|search|advise|guide)\b",
            r"\bplease\s+(?:explain|tell|show|give|find|help|search|advise|guide)\b",
            r"\bwhat\s+is\s+the\s+meaning\s+of\b",
            r"\bwhat\s+does\s+mean\b",
            r"\bhow\s+does\b",
            r"\bdo\s+you\s+know\b",
            r"\bwhat\s+are\s+the\b",
            r"\bexplain\s+the\b",
            r"\bexplain\b",
            r"\bshow\s+me\b",
            r"\bfind\s+me\b",
            r"\bsearch\s+for\b",
            r"\bwhat\s+is\b",
            r"\bwhat\s+are\b",
            r"\bhow\s+to\b",
            r"\bi\s+want\s+to\s+know\b",
        ]
        for filler in fillers:
            normalized = re.sub(filler, "", normalized, flags=re.IGNORECASE)
            
        # Standardize punctuation (clean up questions marks, extra commas)
        normalized = re.sub(r"[?.]", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

# =====================================================================
# Module 2 — Legal Synonym Dictionary
# =====================================================================
class SynonymService:
    """Configurable legal synonym mapping to expand search queries."""
    SYNONYMS = {
        "ipc": "bns bharatiya nyaya sanhita",
        "indian penal code": "bns bharatiya nyaya sanhita",
        "crpc": "bnss bharatiya nagarik suraksha sanhita",
        "code of criminal procedure": "bnss bharatiya nagarik suraksha sanhita",
        "evidence act": "bsa bharatiya sakshya adhiniyam",
        "indian evidence act": "bsa bharatiya sakshya adhiniyam",
        "fundamental rights": "part iii constitution article",
        "murder": "homicide provisions bns section 101",
        "theft": "theft dishonest removal property bns section 303",
        "cyber rules": "it rules intermediary guidelines",
        "it rules 2021": "information technology rules intermediary guidelines"
    }

    @staticmethod
    def expand(query: str) -> str:
        if not query:
            return ""
        expanded = query.lower()
        
        # Word boundary search to prevent replacing sub-parts of words
        for term, expansion in SynonymService.SYNONYMS.items():
            pattern = rf"\b{re.escape(term)}\b"
            if re.search(pattern, expanded):
                expanded = f"{expanded} {expansion}"
                
        # Remove duplicate words in query
        words = []
        for w in expanded.split():
            if w not in words:
                words.append(w)
        return " ".join(words)

# =====================================================================
# Module 3 — Metadata Filter Extraction
# =====================================================================
class MetadataExtractor:
    """Extracts structural filters (law, year, type) to constrain candidate search space."""
    @staticmethod
    def extract(query: str, context: Optional[QueryContext] = None) -> Dict[str, Any]:
        filters = {}
        q_lower = query.lower()
        
        # 1. Target Act Detection
        if any(w in q_lower for w in ("bns", "bharatiya nyaya", "ipc")):
            filters["law"] = "bns"
        elif any(w in q_lower for w in ("bnss", "bharatiya nagarik", "crpc")):
            filters["law"] = "bnss"
        elif any(w in q_lower for w in ("bsa", "bharatiya sakshya", "evidence")):
            filters["law"] = "bsa"
        elif any(w in q_lower for w in ("constitution", "fundamental rights", "article")):
            filters["law"] = "constitution"
        elif any(w in q_lower for w in ("it rules", "intermediary rules", "it_rules")):
            filters["law"] = "it_rules_2021"
        elif "contract" in q_lower:
            filters["law"] = "contract"
        elif "specific relief" in q_lower or "relief act" in q_lower:
            filters["law"] = "specific_relief"
        elif "transfer of property" in q_lower or "property act" in q_lower:
            filters["law"] = "property"
            
        # 2. Year Detection
        year_match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", query)
        if year_match:
            filters["year"] = year_match.group(1)
            
        # 3. Document or Node Type Detection
        if any(w in q_lower for w in ("judgment", "court", "decided", "versus", " v ")):
            filters["document_type"] = "Judgment"
        elif "rule" in q_lower:
            filters["node_type"] = "rule"
        elif "section" in q_lower:
            filters["node_type"] = "section"
        elif "article" in q_lower:
            filters["node_type"] = "article"
            
        # 4. Section/Article Coordinate Extraction
        coord_match = re.search(r"\b(?:section|sec|article|art|rule)\s+(\d+[A-Z]?)\b", q_lower)
        if coord_match:
            filters["number"] = coord_match.group(1)
            
        # Inject explicit context metadata filters if provided
        if context and context.metadata.get("filters"):
            filters.update(context.metadata.get("filters"))
            
        return filters

# =====================================================================
# Module 4 — Query Planner
# =====================================================================
class QueryPlanner:
    """Decides the retrieval routing strategy depending on query intent and scope."""
    @staticmethod
    def plan(context: QueryContext) -> str:
        if context.scope == "user_doc":
            return "user_doc_semantic"
            
        q_lower = context.question.lower()
        
        # Coordinate lookup trigger
        if context.intent == Intent.EXPLAIN_LAW or any(w in q_lower for w in ("section", "article", "rule")):
            if re.search(r"\b(?:section|sec|article|art|rule)\s+(\d+[A-Z]?)\b", q_lower):
                return "coordinate_lookup"
                
        # Case search judgment target
        if context.intent == Intent.CASE_SEARCH or any(w in q_lower for w in ("judgment", "court", "decided", "versus", " v ")):
            return "judgment_hybrid"
            
        return "general_hybrid"

# =====================================================================
# Module 5 — Candidate Retrieval Layer
# =====================================================================
class CoordinateRetriever:
    """Direct lookup of exact sections, articles, or rules in SQLite."""
    @staticmethod
    def retrieve(query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        law = filters.get("law")
        number = filters.get("number")
        
        if not number:
            match = re.search(r"\b(?:section|article|rule|sec|art)\s+(\d+[A-Z]?)\b", query, re.IGNORECASE)
            if match:
                number = match.group(1)
                
        if not number:
            return []
            
        sql = """
        SELECT h.id, h.document_id, h.node_type, h.node_number, h.title, h.text_content
        FROM document_hierarchy h
        WHERE h.node_number LIKE ?
        """
        params = [f"%{number}%"]
        
        if law:
            sql += " AND h.document_id = ?"
            params.append(law)
            
        sql += " LIMIT 5"
        
        nodes = []
        with get_db_conn() as conn:
            cursor = conn.execute(sql, params)
            for row in cursor.fetchall():
                node = dict(row)
                node["score"] = 0.0  # Perfect coordinate match distance
                node["source"] = "coordinate_lookup"
                nodes.append(node)
        return nodes

class SemanticRetriever:
    """Vector database similarity search on ChromaDB."""
    @staticmethod
    def retrieve(query: str, filters: Dict[str, Any], limit: int = 15, collection_name: str = "legal_knowledge_base") -> List[Dict[str, Any]]:
        store = get_vector_store()
        embedding_service = get_embedding_service()
        
        # Build ChromaDB metadata search filter
        where_filter = {}
        
        if collection_name == "case_documents":
            if filters.get("document_id"):
                where_filter["law"] = filters.get("document_id")
            elif filters.get("law"):
                where_filter["law"] = filters.get("law")
        else:
            filter_parts = []
            if filters.get("law"):
                filter_parts.append({"law": filters.get("law")})
            if filters.get("year"):
                filter_parts.append({"year": str(filters.get("year"))})
            if filters.get("node_type"):
                filter_parts.append({"document_type": filters.get("node_type")})
            elif filters.get("document_type") == "Judgment":
                # In ChromaDB global collection, judgment nodes have type mapping
                judgment_types = ["facts", "issues", "arguments", "ratio", "obiter", "holding"]
                # ChromaDB does not support standard $in directly, so we use $or
                filter_parts.append({"$or": [{"document_type": t} for t in judgment_types]})
                
            if len(filter_parts) == 1:
                where_filter = filter_parts[0]
            elif len(filter_parts) > 1:
                where_filter = {"$and": filter_parts}
                
        results = store.search_by_text(
            query_text=query,
            embedding_service=embedding_service,
            collection_name=collection_name,
            n_results=limit,
            where=where_filter if where_filter else None
        )
        
        nodes = []
        if results and results.get("documents"):
            for idx, (doc, meta, dist) in enumerate(zip(results["documents"], results["metadatas"], results["distances"])):
                nodes.append({
                    "id": results["ids"][idx],
                    "document_id": meta.get("law"),
                    "node_type": meta.get("document_type"),
                    "node_number": meta.get("section"),
                    "title": meta.get("title"),
                    "text_content": doc,
                    "score": float(dist),
                    "page": meta.get("page"),
                    "source": "semantic"
                })
        return nodes

class KeywordRetriever:
    """Exact keyword matcher using SQLite FTS5 virtual tables."""
    @staticmethod
    def _ensure_fts_table() -> None:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_hierarchy_fts'")
            exists = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) FROM document_hierarchy")
            total_orig = cursor.fetchone()[0]
            
            count_fts = 0
            if exists:
                cursor.execute("SELECT COUNT(*) FROM document_hierarchy_fts")
                count_fts = cursor.fetchone()[0]
                
            if not exists or count_fts < total_orig:
                log.info(f"FTS5 virtual table missing/incomplete. Building (total items: {total_orig})...")
                cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS document_hierarchy_fts USING fts5(
                    id UNINDEXED,
                    document_id,
                    node_type,
                    node_number,
                    title,
                    text_content
                );
                """)
                cursor.execute("DELETE FROM document_hierarchy_fts")
                cursor.execute("""
                INSERT INTO document_hierarchy_fts (id, document_id, node_type, node_number, title, text_content)
                SELECT id, document_id, node_type, node_number, title, text_content
                FROM document_hierarchy
                """)
                conn.commit()
                log.info("FTS5 table successfully initialized.")

    @staticmethod
    def retrieve(query: str, filters: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
        KeywordRetriever._ensure_fts_table()
        
        # Split terms and build match syntax
        words = [w.strip() for w in re.split(r'\W+', query) if len(w.strip()) > 2]
        if not words:
            return []
            
        # Wrap words in double quotes to prevent syntax issues
        fts_terms = [f'"{w}"' for w in words]
        fts_query = " OR ".join(fts_terms)
        
        sql = """
        SELECT id, document_id, node_type, node_number, title, text_content, bm25(document_hierarchy_fts) AS score
        FROM document_hierarchy_fts
        WHERE document_hierarchy_fts MATCH ?
        """
        params = [fts_query]
        
        if filters.get("law"):
            sql += " AND document_id = ?"
            params.append(filters.get("law"))
            
        if filters.get("node_type"):
            sql += " AND node_type = ?"
            params.append(filters.get("node_type"))
        elif filters.get("document_type") == "Judgment":
            sql += " AND node_type IN ('facts', 'issues', 'arguments', 'ratio', 'obiter', 'holding')"
            
        sql += " ORDER BY score ASC LIMIT ?"
        params.append(limit)
        
        nodes = []
        with get_db_conn() as conn:
            cursor = conn.execute(sql, params)
            for row in cursor.fetchall():
                node = dict(row)
                node["source"] = "keyword"
                nodes.append(node)
        return nodes

# =====================================================================
# Module 6 — Rank Fusion (RRF)
# =====================================================================
class RankFusion:
    """Combines ranks from vector and lexical results using Reciprocal Rank Fusion."""
    @staticmethod
    def merge(semantic_nodes: List[Dict[str, Any]], keyword_nodes: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
        rrf_scores = {}
        node_lookup = {}
        provenance = {}
        
        # Accumulate semantic ranks
        for rank, node in enumerate(semantic_nodes, 1):
            nid = node["id"]
            node_lookup[nid] = node
            rrf_scores[nid] = rrf_scores.get(nid, 0.0) + (1.0 / (k + rank))
            provenance[nid] = provenance.get(nid, {})
            provenance[nid]["semantic_rank"] = rank
            provenance[nid]["semantic_score"] = node.get("score")
            
        # Accumulate keyword ranks
        for rank, node in enumerate(keyword_nodes, 1):
            nid = node["id"]
            if nid not in node_lookup:
                node_lookup[nid] = node
            rrf_scores[nid] = rrf_scores.get(nid, 0.0) + (1.0 / (k + rank))
            provenance[nid] = provenance.get(nid, {})
            provenance[nid]["keyword_rank"] = rank
            provenance[nid]["keyword_score"] = node.get("score")
            
        # Sort top nodes
        sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        fused_nodes = []
        for rank_idx, (nid, rrf_score) in enumerate(sorted_ids, 1):
            node = node_lookup[nid]
            node["rrf_score"] = rrf_score
            node["rrf_rank"] = rank_idx
            node["provenance"] = provenance[nid]
            
            # Identify source
            if "semantic_rank" in provenance[nid] and "keyword_rank" in provenance[nid]:
                node["source"] = "hybrid"
            elif "semantic_rank" in provenance[nid]:
                node["source"] = "semantic"
            else:
                node["source"] = "keyword"
                
            fused_nodes.append(node)
        return fused_nodes

# =====================================================================
# Module 7 — Cross Encoder Reranker
# =====================================================================
class Reranker:
    """Optional cross encoder model to re-score candidate relevance."""
    @staticmethod
    def rank(query: str, candidates: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        if not candidates:
            return []
            
        # Fallback scoring: combines lexical match overlap with the RRF score
        query_words = set(query.lower().split())
        for node in candidates:
            if node.get("source") == "coordinate_lookup":
                node["rerank_score"] = 1.0
                continue
                
            text = node.get("text_content", "").lower()
            overlap = sum(1 for w in query_words if w in text)
            overlap_ratio = overlap / len(query_words) if query_words else 0.0
            
            # Combine overlap and reciprocal rank score
            node["rerank_score"] = (0.75 * overlap_ratio) + (0.25 * node.get("rrf_score", 0.0))
            
        reranked = sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return reranked[:limit]

# =====================================================================
# Module 8 — Dynamic Context Builder
# =====================================================================
class ContextBuilder:
    """Assembles rich hierarchical metadata, siblings, and child structures for nodes."""
    @staticmethod
    def build(nodes: List[Dict[str, Any]], token_limit: int = 4000) -> List[Dict[str, Any]]:
        built_nodes = []
        current_tokens = 0
        
        with get_db_conn() as conn:
            for node in nodes:
                node_text = node.get("text_content", "")
                approx_tokens = len(node_text) // 4
                if current_tokens + approx_tokens > token_limit:
                    break
                    
                node_id = node.get("id")
                node_type = node.get("node_type")
                doc_id = node.get("document_id")
                
                # Statute/Rule Assembly
                if doc_id and node_type in ("section", "article", "rule", "subsection", "sub_rule", "clause", "proviso", "explanation"):
                    # Retrieve breadcrumbs
                    cursor = conn.execute("SELECT parent_node_id, title, node_number FROM document_hierarchy WHERE id = ?", (node_id,))
                    row = cursor.fetchone()
                    breadcrumbs = ""
                    if row:
                        parent_id = row["parent_node_id"]
                        chain = []
                        while parent_id:
                            p_cursor = conn.execute("SELECT node_number, title, parent_node_id FROM document_hierarchy WHERE id = ?", (parent_id,))
                            p_row = p_cursor.fetchone()
                            if p_row:
                                chain.append(f"{p_row['node_number'] or ''} {p_row['title'] or ''}".strip())
                                parent_id = p_row["parent_node_id"]
                            else:
                                break
                        if chain:
                            breadcrumbs = " > ".join(reversed(chain))
                            
                    # Retrieve subsections, provisos, explanations
                    child_cursor = conn.execute(
                        "SELECT node_type, node_number, text_content FROM document_hierarchy WHERE parent_node_id = ? ORDER BY index_order ASC",
                        (node_id,)
                    )
                    children = child_cursor.fetchall()
                    
                    # Construct markdown context
                    context_md = f"### {node.get('node_number', '')} {node.get('title', '')}\n"
                    if breadcrumbs:
                        context_md += f"*Path: {breadcrumbs}*\n"
                    context_md += f"\n{node_text}\n"
                    
                    if children:
                        context_md += "\n*Subsections & Explanations:*\n"
                        for child in children:
                            c_num = child["node_number"] or child["node_type"].capitalize()
                            context_md += f"- **{c_num}**: {child['text_content']}\n"
                            
                    node["text_content"] = context_md
                    
                # Judgment Assembly
                elif doc_id and node_type in ("facts", "issues", "arguments", "ratio", "obiter", "holding"):
                    cursor = conn.execute("SELECT title FROM documents WHERE id = ?", (doc_id,))
                    row = cursor.fetchone()
                    case_name = row["title"] if row else "Judgment Record"
                    
                    context_md = f"### Judgment Segment: {node.get('title', '')}\n"
                    context_md += f"*Case Name: {case_name}*\n\n"
                    context_md += node_text
                    node["text_content"] = context_md
                    
                # User Uploaded Documents
                elif node.get("page"):
                    context_md = f"### Document: {node.get('title', '')} (Page {node.get('page')})\n\n"
                    context_md += node_text
                    node["text_content"] = context_md
                    
                built_nodes.append(node)
                current_tokens += approx_tokens
        return built_nodes

# =====================================================================
# Module 9 — Reference Expansion Engine
# =====================================================================
class ReferenceExpander:
    """Enriches context with cited documents and cross-references up to depth D."""
    @staticmethod
    def expand(nodes: List[Dict[str, Any]], depth: int = 1) -> List[Dict[str, Any]]:
        expanded = []
        seen_ids = set()
        
        with get_db_conn() as conn:
            for node in nodes:
                nid = node.get("id")
                if not nid or nid in seen_ids:
                    continue
                seen_ids.add(nid)
                
                # Fetch cross-references
                cursor = conn.execute("""
                    SELECT r.citation_text, r.reference_type, h.id as target_id, h.node_number, h.title, h.text_content
                    FROM cross_references r
                    JOIN document_hierarchy h ON r.target_node_id = h.id
                    WHERE r.source_node_id = ?
                """, (nid,))
                
                references = []
                for row in cursor.fetchall():
                    ref = dict(row)
                    references.append(ref)
                    
                    # Traverse depth
                    if depth > 1 and ref["target_id"] not in seen_ids:
                        seen_ids.add(ref["target_id"])
                        
                node["references"] = references
                expanded.append(node)
        return expanded

# =====================================================================
# Module 10 — Retrieval Confidence Calculator
# =====================================================================
class ConfidenceCalculator:
    """Calculates float confidence metric (0-1) and categorical confidence level."""
    @staticmethod
    def compute(node: Dict[str, Any], query: str) -> Dict[str, Any]:
        source = node.get("source", "unknown")
        score = 0.5
        level = "Medium"
        
        if source == "coordinate_lookup":
            score = 1.0
            level = "High"
        elif source == "hybrid":
            score = 0.90
            level = "High"
        elif source == "semantic":
            distance = node.get("score", 1.0)
            if distance < 0.6:
                score = 0.80
                level = "High"
            elif distance < 1.0:
                score = 0.60
                level = "Medium"
            else:
                score = 0.40
                level = "Low"
        elif source == "keyword":
            bm_score = node.get("score", 0.0)
            if bm_score < -15:
                score = 0.75
                level = "High"
            elif bm_score < -8:
                score = 0.55
                level = "Medium"
            else:
                score = 0.35
                level = "Low"
                
        node["confidence_score"] = score
        node["confidence_category"] = level
        return node

# =====================================================================
# Module 11 — Retrieval Explanation Builder
# =====================================================================
class ExplanationBuilder:
    """Constructs debug-friendly metadata details of ranks and scores for developers."""
    @staticmethod
    def build(node: Dict[str, Any], dev_mode: bool = False) -> Dict[str, Any]:
        if not dev_mode:
            if "explanation" in node:
                del node["explanation"]
            return node
            
        provenance = node.get("provenance", {})
        node["explanation"] = {
            "retrieval_source": node.get("source"),
            "semantic_rank": provenance.get("semantic_rank", "N/A"),
            "semantic_distance": provenance.get("semantic_score", "N/A"),
            "keyword_rank": provenance.get("keyword_rank", "N/A"),
            "keyword_bm25": provenance.get("keyword_score", "N/A"),
            "rrf_score": node.get("rrf_score", "N/A"),
            "final_rank": node.get("rrf_rank", "N/A"),
            "confidence_score": node.get("confidence_score", 0.5)
        }
        return node

# =====================================================================
# Module 12 — Retrieval Cache
# =====================================================================
class RetrievalCache:
    """Caches search nodes with cache invalidation bound to the database row signatures."""
    _cache = {}
    _signature = None

    @staticmethod
    def _db_signature() -> str:
        try:
            with get_db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*), SUM(rowid) FROM document_hierarchy")
                row = cursor.fetchone()
                return f"{row[0]}-{row[1]}"
        except Exception:
            return "stale-fallback"

    @staticmethod
    def get(query: str, filters: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        current_sig = RetrievalCache._db_signature()
        if RetrievalCache._signature != current_sig:
            RetrievalCache._cache.clear()
            RetrievalCache._signature = current_sig
            return None
            
        cache_key = (query, tuple(sorted(filters.items())))
        return RetrievalCache._cache.get(cache_key)

    @staticmethod
    def set(query: str, filters: Dict[str, Any], results: List[Dict[str, Any]]) -> None:
        current_sig = RetrievalCache._db_signature()
        RetrievalCache._signature = current_sig
        
        # Clear cache if it grows past 100 queries
        if len(RetrievalCache._cache) > 100:
            RetrievalCache._cache.clear()
            
        cache_key = (query, tuple(sorted(filters.items())))
        RetrievalCache._cache[cache_key] = results

# =====================================================================
# Module 13 — Service Interface (Main Retriever Coordination)
# =====================================================================
class Retriever:
    """
    Production-grade hybrid retriever coordinating preprocessing, plan generation,
    vector & exact candidates search, rank fusion, context assembly, and explanation builders.
    """
    @staticmethod
    def retrieve(context: QueryContext) -> List[Dict[str, Any]]:
        context.start_stage("retrieval")
        try:
            log.info(f"Incoming query: '{context.question}' [Intent: {context.intent}]")
            
            # Module 1: Preprocess query
            normalized_query = QueryNormalizer.normalize(context.question)
            
            # Module 2: Synonym expansion
            expanded_query = SynonymService.expand(normalized_query)
            log.info(f"Normalized/Expanded query: '{expanded_query}'")
            
            # Module 3: Extract metadata filters
            filters = MetadataExtractor.extract(expanded_query, context)
            
            # Module 4: Plan retrieval strategy
            strategy = QueryPlanner.plan(context)
            log.info(f"Selected retrieval strategy: '{strategy}' with filters: {filters}")
            
            # Module 12: Cache lookup
            cached = RetrievalCache.get(expanded_query, filters)
            if cached is not None:
                log.info(f"Cache hit! Returning {len(cached)} cached nodes.")
                context.retrieved_nodes = cached
                return cached
                
            # Module 5: Execute Candidate Retrieval
            candidates = []
            
            if strategy == "coordinate_lookup":
                log.info("Executing coordinate lookup strategy...")
                candidates = CoordinateRetriever.retrieve(expanded_query, filters)
                # Fallback to general hybrid if no exact coordinate found
                if not candidates:
                    log.info("No exact coordinate node found. Falling back to hybrid search.")
                    strategy = "general_hybrid"
                    
            if strategy == "user_doc_semantic":
                log.info("Executing user document hybrid search (Step 5)...")
                
                # 1. Semantic candidates
                semantic_candidates = SemanticRetriever.retrieve(
                    query=context.question, 
                    filters={"document_id": context.document_id},
                    limit=12,
                    collection_name="case_documents"
                )
                
                # 2. Local SQLite keyword candidates fallback
                from app.models.database import get_user_document_chunks
                db_chunks = get_user_document_chunks(context.document_id)
                
                # Split terms and build overlap
                query_words = [w.strip().lower() for w in re.split(r'\W+', context.question) if len(w.strip()) > 2]
                
                keyword_candidates = []
                for chunk in db_chunks:
                    text = chunk["chunk_text"].lower()
                    overlap = sum(1 for w in query_words if w in text)
                    if overlap > 0:
                        keyword_candidates.append({
                            "id": chunk["id"],
                            "document_id": chunk["document_id"],
                            "node_type": "user_document",
                            "node_number": f"Page {chunk['page_number']}",
                            "title": "", # resolved to filename later
                            "text_content": chunk["chunk_text"],
                            "score": float(overlap),
                            "page": chunk["page_number"],
                            "source": "keyword"
                        })
                # Sort keyword candidates by overlap score descending
                keyword_candidates.sort(key=lambda x: x["score"], reverse=True)
                keyword_candidates = keyword_candidates[:12]
                
                # 3. Merge semantic & keyword results using RRF rank fusion
                k = 60
                scores = {}
                node_map = {}
                provenance = {}
                
                for rank, node in enumerate(semantic_candidates, 1):
                    nid = node["id"]
                    node_map[nid] = node
                    scores[nid] = scores.get(nid, 0.0) + (1.0 / (k + rank))
                    provenance[nid] = provenance.get(nid, {})
                    provenance[nid]["semantic_rank"] = rank
                    provenance[nid]["semantic_score"] = node.get("score")
                    
                for rank, node in enumerate(keyword_candidates, 1):
                    nid = node["id"]
                    if nid not in node_map:
                        node_map[nid] = node
                    scores[nid] = scores.get(nid, 0.0) + (1.0 / (k + rank))
                    provenance[nid] = provenance.get(nid, {})
                    provenance[nid]["keyword_rank"] = rank
                    provenance[nid]["keyword_score"] = node.get("score")
                    
                sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                
                candidates = []
                for rank_idx, (nid, r_score) in enumerate(sorted_nodes, 1):
                    node = node_map[nid]
                    node["rrf_score"] = r_score
                    node["rrf_rank"] = rank_idx
                    node["provenance"] = provenance[nid]
                    if "semantic_rank" in provenance[nid] and "keyword_rank" in provenance[nid]:
                        node["source"] = "hybrid"
                    elif "semantic_rank" in provenance[nid]:
                        node["source"] = "semantic"
                    else:
                        node["source"] = "keyword"
                    candidates.append(node)
                
                # Step 4 Logging of retrieved chunks
                log.info(
                    f"Q&A Retrieved Chunks (Step 4) — Query: '{context.question}' | "
                    f"DocumentID Filter: {context.document_id} | Chunks Retrieved: {len(candidates)}"
                )
                for c_node in candidates:
                    log.info(
                        f"Retrieved Chunk details — ID: {c_node['id']} | Page: {c_node.get('page')} | "
                        f"Score: {c_node.get('score')} | RRF Score: {c_node.get('rrf_score', 0.0)} | "
                        f"Text excerpt (first 500 chars): {repr(c_node['text_content'][:500])}"
                    )
                
            elif strategy == "judgment_hybrid":
                log.info("Executing judgment hybrid search...")
                filters["document_type"] = "Judgment"
                semantic_candidates = SemanticRetriever.retrieve(expanded_query, filters, limit=15)
                keyword_candidates = KeywordRetriever.retrieve(expanded_query, filters, limit=20)
                # Module 6: Rank Fusion
                candidates = RankFusion.merge(semantic_candidates, keyword_candidates)
                
            elif strategy == "general_hybrid":
                log.info("Executing general hybrid search...")
                semantic_candidates = SemanticRetriever.retrieve(expanded_query, filters, limit=15)
                keyword_candidates = KeywordRetriever.retrieve(expanded_query, filters, limit=20)
                # Module 6: Rank Fusion
                candidates = RankFusion.merge(semantic_candidates, keyword_candidates)
                
            # Module 7: Cross Encoder Reranker
            reranked_candidates = Reranker.rank(expanded_query, candidates, limit=8)
            
            # Module 8: Dynamic Context Builder
            context_nodes = ContextBuilder.build(reranked_candidates)
            
            # Module 9: Reference Expansion
            expanded_nodes = ReferenceExpander.expand(context_nodes, depth=1)
            
            # Modules 10 & 11: Compute confidence and dev explanations
            final_nodes = []
            is_dev = context.metadata.get("dev_mode", False)
            for node in expanded_nodes:
                node = ConfidenceCalculator.compute(node, expanded_query)
                node = ExplanationBuilder.build(node, dev_mode=is_dev)
                final_nodes.append(node)
                
            # Module 12: Write to cache
            RetrievalCache.set(expanded_query, filters, final_nodes)
            
            # Save and return
            context.retrieved_nodes = final_nodes
            log.info(f"Retrieval pipeline complete. Retrieved {len(final_nodes)} nodes.")
            return final_nodes
            
        except Exception as e:
            log.error(f"Retrieval engine execution failure: {e}", exc_info=True)
            context.errors.append(f"Retrieval error: {str(e)}")
            raise RetrievalError(f"Failed to query hybrid retrieval pipeline: {str(e)}")
        finally:
            context.end_stage("retrieval")
