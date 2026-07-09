import re
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.models.database import get_db_conn, insert_cross_reference
from app.models.context import QueryContext
from app.utils.logging import get_logger

def extract_and_link_references():
    """
    Scans all text_content in document_hierarchy, extracts citations,
    resolves target nodes in SQLite, and populates the cross_references table.
    """
    print("======================================================================")
    print("🔗  STEP 4.5: Extracting and Linking Cross-References")
    print("======================================================================")
    
    # 1. Fetch all hierarchy nodes from DB
    nodes = []
    with get_db_conn() as conn:
        cursor = conn.execute("SELECT id, text_content, document_id FROM document_hierarchy")
        nodes = [dict(row) for row in cursor.fetchall()]
        
    print(f"  Scanning {len(nodes)} hierarchy nodes for citation references...")
    
    # Pre-compile patterns
    patterns = {
        "constitution_article": re.compile(r"\bArticle\s+(\d+[A-Z]?)\b", re.IGNORECASE),
        "bns_section": re.compile(r"\bSection\s+(\d+[A-Z]?)\b(?:\s+of\s+(?:the\s+)?Bharatiya\s+Nyaya\s+Sanhita|\s+BNS)\b", re.IGNORECASE),
        "bnss_section": re.compile(r"\bSection\s+(\d+[A-Z]?)\b(?:\s+of\s+(?:the\s+)?Bharatiya\s+Nagarik\s+Suraksha\s+Sanhita|\s+BNSS)\b", re.IGNORECASE),
        "bsa_section": re.compile(r"\bSection\s+(\d+[A-Z]?)\b(?:\s+of\s+(?:the\s+)?Bharatiya\s+Sakshya\s+Adhiniyam|\s+BSA)\b", re.IGNORECASE),
        "act_section": re.compile(r"\bSection\s+(\d+[A-Z]?)\s+of\s+(?:the\s+)?([A-Za-z\s]+?)\s+Act\b", re.IGNORECASE),
    }

    links_created = 0
    
    # Resolve helper: finds target node_id in DB if it exists
    def find_target_node(doc_type_key, item_num):
        with get_db_conn() as conn:
            cursor = conn.execute("""
            SELECT id FROM document_hierarchy 
            WHERE document_id = ? AND node_number LIKE ?
            LIMIT 1
            """, (doc_type_key, f"%{item_num}%"))
            row = cursor.fetchone()
            if row:
                return row["id"]
        return None

    # Resolve act helper by matching name
    def find_doc_id_by_name(act_name):
        act_name_clean = act_name.lower().strip()
        with get_db_conn() as conn:
            cursor = conn.execute("""
            SELECT id FROM documents 
            WHERE title LIKE ? OR short_title LIKE ? 
            LIMIT 1
            """, (f"%{act_name_clean}%", f"%{act_name_clean}%"))
            row = cursor.fetchone()
            if row:
                return row["id"]
        return None

    for node in nodes:
        node_id = node["id"]
        text = node["text_content"]
        
        # 1. Constitution Article References
        for match in patterns["constitution_article"].finditer(text):
            art_num = match.group(1)
            citation = f"Article {art_num} of the Constitution"
            target_id = find_target_node("constitution", art_num)
            insert_cross_reference(
                source_node_id=node_id,
                citation_text=citation,
                target_node_id=target_id,
                reference_type="cites_statute"
            )
            links_created += 1
            
        # 2. BNS Section References
        for match in patterns["bns_section"].finditer(text):
            sec_num = match.group(1)
            citation = f"Section {sec_num} BNS"
            target_id = find_target_node("bns", sec_num)
            insert_cross_reference(
                source_node_id=node_id,
                citation_text=citation,
                target_node_id=target_id,
                reference_type="cites_statute"
            )
            links_created += 1

        # 3. BNSS Section References
        for match in patterns["bnss_section"].finditer(text):
            sec_num = match.group(1)
            citation = f"Section {sec_num} BNSS"
            target_id = find_target_node("bnss", sec_num)
            insert_cross_reference(
                source_node_id=node_id,
                citation_text=citation,
                target_node_id=target_id,
                reference_type="cites_statute"
            )
            links_created += 1

        # 4. BSA Section References
        for match in patterns["bsa_section"].finditer(text):
            sec_num = match.group(1)
            citation = f"Section {sec_num} BSA"
            target_id = find_target_node("bsa", sec_num)
            insert_cross_reference(
                source_node_id=node_id,
                citation_text=citation,
                target_node_id=target_id,
                reference_type="cites_statute"
            )
            links_created += 1

        # 5. General Act Section References
        for match in patterns["act_section"].finditer(text):
            sec_num = match.group(1)
            act_name = match.group(2)
            citation = f"Section {sec_num} of the {act_name} Act"
            
            target_doc_id = find_doc_id_by_name(act_name)
            target_id = None
            if target_doc_id:
                target_id = find_target_node(target_doc_id, sec_num)
                
            insert_cross_reference(
                source_node_id=node_id,
                citation_text=citation,
                target_node_id=target_id,
                reference_type="cites_statute"
            )
            links_created += 1

    print(f"  ✅ Extracted and linked {links_created} cross-references.")

class ReferenceService:
    """
    Enriches query context by pulling hierarchy coordinates (parent/child)
    and resolved outbound/inbound citations and version histories from SQLite.
    """
    
    @staticmethod
    def expand(context: QueryContext) -> List[Dict[str, Any]]:
        """
        Enriches retrieved nodes in context.retrieved_nodes and stores
        the results in context.expanded_nodes.
        """
        context.start_stage("reference_expansion")
        log = get_logger("reference_service")
        try:
            log.info(f"Expanding coordinates for {len(context.retrieved_nodes)} retrieved nodes...")
            expanded = []
            seen_node_ids = set()
            
            with get_db_conn() as conn:
                for node in context.retrieved_nodes:
                    node_id = node["id"]
                    if node_id in seen_node_ids:
                        continue
                    seen_node_ids.add(node_id)
                    
                    # Fetch hierarchy details
                    cursor = conn.execute("SELECT * FROM document_hierarchy WHERE id = ?", (node_id,))
                    row = cursor.fetchone()
                    if not row:
                        # Fallback for dynamic nodes
                        expanded.append(node)
                        continue
                    node_data = dict(row)
                    
                    # Preserve original score if present
                    if "score" in node:
                        node_data["score"] = node["score"]
                    if "page" in node:
                        node_data["page"] = node["page"]
                    
                    # 1. Trace Parent Hierarchy (Breadcrumbs)
                    parent_chain = []
                    curr_parent_id = node_data["parent_node_id"]
                    while curr_parent_id:
                        p_cursor = conn.execute("SELECT id, node_type, node_number, title, parent_node_id FROM document_hierarchy WHERE id = ?", (curr_parent_id,))
                        p_row = p_cursor.fetchone()
                        if p_row:
                            parent_chain.append(dict(p_row))
                            curr_parent_id = p_row["parent_node_id"]
                        else:
                            break
                    node_data["parents"] = list(reversed(parent_chain))
                    
                    # 2. Retrieve Children (Subsections, Clauses, etc.)
                    child_cursor = conn.execute("SELECT * FROM document_hierarchy WHERE parent_node_id = ? ORDER BY index_order ASC", (node_id,))
                    node_data["children"] = [dict(r) for r in child_cursor.fetchall()]
                    
                    # 3. Outbound & Inbound Citations
                    outbound_cursor = conn.execute("""
                        SELECT r.citation_text, r.reference_type, h.node_number as target_num, d.title as target_doc
                        FROM cross_references r
                        LEFT JOIN document_hierarchy h ON r.target_node_id = h.id
                        LEFT JOIN documents d ON h.document_id = d.id
                        WHERE r.source_node_id = ?
                    """, (node_id,))
                    node_data["outbound_references"] = [dict(r) for r in outbound_cursor.fetchall()]
                    
                    inbound_cursor = conn.execute("""
                        SELECT r.citation_text, r.reference_type, h.node_number as source_num, d.title as source_doc
                        FROM cross_references r
                        JOIN document_hierarchy h ON r.source_node_id = h.id
                        JOIN documents d ON h.document_id = d.id
                        WHERE r.target_node_id = ?
                    """, (node_id,))
                    node_data["inbound_references"] = [dict(r) for r in inbound_cursor.fetchall()]
                    
                    # 4. Version History
                    version_cursor = conn.execute("SELECT * FROM document_versions WHERE node_id = ?", (node_id,))
                    node_data["versions"] = [dict(r) for r in version_cursor.fetchall()]
                    
                    expanded.append(node_data)
                    
            context.expanded_nodes = expanded
            log.info(f"Successfully expanded {len(expanded)} nodes.")
            return expanded
        except Exception as e:
            log.error(f"Reference expansion failed: {e}", exc_info=True)
            context.errors.append(f"Reference expansion failed: {str(e)}")
            context.expanded_nodes = context.retrieved_nodes
            return context.retrieved_nodes
        finally:
            context.end_stage("reference_expansion")
