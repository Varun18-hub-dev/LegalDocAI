from typing import List, Dict, Any
from app.models.database import get_db_conn
from app.models.context import QueryContext
from app.utils.logging import get_logger

log = get_logger("citation_formatter")

class CitationFormatter:
    """
    De-duplicates and structures retrieved source coordinates into a standard format,
    appending citation footnotes to the final generated text.
    """
    
    @staticmethod
    def format(context: QueryContext) -> List[Dict[str, Any]]:
        """
        Public contract method to format citations.
        Saves formatted citations in context.citations and context.formatted_answer.
        """
        context.start_stage("citation_formatting")
        try:
            log.info("Formatting citations...")
            citations = []
            seen_keys = set()
            seen_pages = set()
            
            # Determine source node list
            source_nodes = context.expanded_nodes if context.expanded_nodes else context.retrieved_nodes
            
            if not source_nodes:
                context.citations = []
                context.formatted_answer = context.llm_response
                return []
                
            with get_db_conn() as conn:
                for node in source_nodes:
                    node_id = node.get("id")
                    doc_id = node.get("document_id")
                    node_num = node.get("node_number", "")
                    
                    if context.scope == "user_doc":
                        page_num = node.get("page")
                        if page_num in seen_pages:
                            continue
                        seen_pages.add(page_num)
                    else:
                        # Deduplicate key
                        key = f"{doc_id}_{node_num}"
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)
                    
                    # Fetch document details from SQLite documents table
                    doc_title = ""
                    doc_short = ""
                    doc_type_db = ""
                    cursor = conn.execute("SELECT title, short_title, document_type FROM documents WHERE id = ?", (doc_id,))
                    doc_row = cursor.fetchone()
                    if doc_row:
                        doc_title = doc_row["title"]
                        doc_short = doc_row["short_title"]
                        doc_type_db = doc_row["document_type"]
                        
                    citation_entry = {
                        "index": len(citations) + 1,
                        "document_id": doc_id,
                        "node_id": node_id
                    }
                    
                    if context.scope == "user_doc":
                        # User contract/PDF citation
                        citation_entry.update({
                            "type": "user_document",
                            "filename": doc_title or doc_id,
                            "page": node.get("page"),
                            "snippet": node.get("text_content", "")[:150] + "..."
                        })
                    elif doc_type_db == "Judgment":
                        # Judicial case law
                        citation_entry.update({
                            "type": "judgment",
                            "case_name": doc_title,
                            "citation": doc_short or "Supreme Court",
                            "segment": node_num,
                            "snippet": node.get("text_content", "")[:150] + "..."
                        })
                    elif doc_type_db == "Notification":
                        # Government notification
                        citation_entry.update({
                            "type": "notification",
                            "title": doc_title,
                            "number": doc_short or doc_id,
                            "snippet": node.get("text_content", "")[:150] + "..."
                        })
                    else:
                        # Statutes and Acts (Civil, Criminal, Rules)
                        citation_entry.update({
                            "type": "statute",
                            "act_name": doc_title,
                            "coordinate": node_num,
                            "title": node.get("title", ""),
                            "snippet": node.get("text_content", "")[:150] + "..."
                        })
                        
                    citations.append(citation_entry)
                    
            context.citations = citations
            
            # Format LLM response with clean footnote links
            raw_answer = context.llm_response or ""
            if citations:
                footnotes = ["\n\n### 🔗 Sources & Citations:"]
                for c in citations:
                    if c["type"] == "user_document":
                        footnotes.append(f"*{c['index']}. [{c['filename']}] (Page {c['page']})*")
                    elif c["type"] == "judgment":
                        footnotes.append(f"*{c['index']}. {c['case_name']} ({c['citation']}) — Segment: {c['segment']}*")
                    elif c["type"] == "notification":
                        footnotes.append(f"*{c['index']}. {c['title']} ({c['number']})*")
                    else:
                        footnotes.append(f"*{c['index']}. {c['coordinate']} \"{c['title']}\" — {c['act_name']}*")
                context.formatted_answer = raw_answer + "\n" + "\n".join(footnotes)
            else:
                context.formatted_answer = raw_answer
                
            log.info(f"Formatted {len(citations)} unique citations.")
            return citations
        except Exception as e:
            log.error(f"Citation formatting failed: {e}", exc_info=True)
            context.formatted_answer = context.llm_response
            return []
        finally:
            context.end_stage("citation_formatting")
