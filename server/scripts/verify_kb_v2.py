import sys
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.database import get_db_conn, get_document, get_document_nodes, get_node_references, get_incoming_references, get_node_versions
from scripts.embedding_service import get_embedding_service
from scripts.vector_store import get_vector_store

def verify_kb_v2():
    print("=" * 80)
    print("🔍  LegalDocAI - Knowledge Base v2.0 Verification")
    print("=" * 80)

    # ------------------------------------------------------------
    # 1. Verify Documents & Hierarchy
    # ------------------------------------------------------------
    print("\n📊 1. Relational Database Statistics:")
    
    with get_db_conn() as conn:
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        node_count = conn.execute("SELECT COUNT(*) FROM document_hierarchy").fetchone()[0]
        version_count = conn.execute("SELECT COUNT(*) FROM document_versions").fetchone()[0]
        ref_count = conn.execute("SELECT COUNT(*) FROM cross_references").fetchone()[0]
        
        print(f"   Documents: {doc_count}")
        print(f"   Hierarchy Nodes: {node_count}")
        print(f"   Version History Entries: {version_count}")
        print(f"   Cross-Reference Links: {ref_count}")
        
        # Breakdown by doc type
        cursor = conn.execute("SELECT document_type, COUNT(*) FROM documents GROUP BY document_type")
        for row in cursor.fetchall():
            print(f"     - {row[0]}: {row[1]}")
            
    # ------------------------------------------------------------
    # 2. Verify Hierarchical Parsing
    # ------------------------------------------------------------
    print("\n🌳 2. Verifying Tree Hierarchy:")
    with get_db_conn() as conn:
        # Get a section node and trace its parent tree
        cursor = conn.execute("""
        SELECT h1.id, h1.node_type, h1.node_number, h1.title, h1.parent_node_id, d.title as doc_title
        FROM document_hierarchy h1
        JOIN documents d ON h1.document_id = d.id
        WHERE h1.node_type = 'section' OR h1.node_type = 'article'
        LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            print(f"   Section Node Found: '{row['node_number']} {row['title']}' under '{row['doc_title']}'")
            # Trace parent
            parent_id = row["parent_node_id"]
            while parent_id:
                p_cursor = conn.execute("SELECT node_type, node_number, title, parent_node_id FROM document_hierarchy WHERE id = ?", (parent_id,))
                p_row = p_cursor.fetchone()
                if p_row:
                    print(f"     └─ Parent: [{p_row['node_type'].upper()}] {p_row['node_number'] or ''} {p_row['title'] or ''}")
                    parent_id = p_row["parent_node_id"]
                else:
                    break
        else:
            print("   ❌ No section/article nodes found in database.")

    # ------------------------------------------------------------
    # 3. Verify Judgment Parsing
    # ------------------------------------------------------------
    print("\n⚖️ 3. Verifying SC Judgment Structure:")
    with get_db_conn() as conn:
        cursor = conn.execute("SELECT id, title, metadata FROM documents WHERE document_type = 'Judgment' LIMIT 1")
        row = cursor.fetchone()
        if row:
            print(f"   Judgment Found: '{row['title']}'")
            # Check hierarchy parts
            parts_cursor = conn.execute("SELECT node_type, title, length(text_content) FROM document_hierarchy WHERE document_id = ?", (row["id"],))
            for p in parts_cursor.fetchall():
                print(f"     - Segment [{p[0]}]: '{p[1]}' ({p[2]} characters)")
        else:
            print("   ❌ No Judgment records found in database.")

    # ------------------------------------------------------------
    # 4. Verify Citation Linking
    # ------------------------------------------------------------
    print("\n🔗 4. Verifying Cross-References & Citations:")
    with get_db_conn() as conn:
        # Get some sample cross references
        cursor = conn.execute("""
        SELECT r.citation_text, r.reference_type, h_src.node_number as src_num, d_src.title as src_doc,
               h_tgt.node_number as tgt_num, d_tgt.title as tgt_doc
        FROM cross_references r
        JOIN document_hierarchy h_src ON r.source_node_id = h_src.id
        JOIN documents d_src ON h_src.document_id = d_src.id
        LEFT JOIN document_hierarchy h_tgt ON r.target_node_id = h_tgt.id
        LEFT JOIN documents d_tgt ON h_tgt.document_id = d_tgt.id
        LIMIT 5
        """)
        rows = cursor.fetchall()
        if rows:
            for idx, r in enumerate(rows, 1):
                link_status = f"RESOLVED ➔ {r['tgt_doc']} {r['tgt_num'] or ''}" if r['tgt_num'] else "UNRESOLVED (External)"
                print(f"   [{idx}] Source: {r['src_doc']} {r['src_num'] or ''}")
                print(f"       Citation: '{r['citation_text']}' ({r['reference_type']})")
                print(f"       Status: {link_status}")
                print("-" * 50)
        else:
            print("   ❌ No cross-reference records found.")

    # ------------------------------------------------------------
    # 5. Semantic Vector Search Verification
    # ------------------------------------------------------------
    print("\n🎯 5. Running Semantic Search Query Verification:")
    embedding_service = get_embedding_service()
    store = get_vector_store()
    print("\n📜 6. Verifying IT Rules and Nested Subelements:")
    with get_db_conn() as conn:
        # Check rule 3 node
        cursor = conn.execute("""
        SELECT h1.id, h1.node_type, h1.node_number, h1.title, h1.parent_node_id
        FROM document_hierarchy h1
        WHERE h1.document_id = 'it_rules_2021' AND h1.node_type = 'rule' AND h1.node_number LIKE '%Rule 3%'
        LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            print(f"   Rule Node Found: '{row['node_number']} {row['title']}'")
            # Trace sub-rules
            sub_cursor = conn.execute("""
            SELECT id, node_type, node_number, title, parent_node_id 
            FROM document_hierarchy 
            WHERE parent_node_id = ?
            """, (row["id"],))
            sub_rows = sub_cursor.fetchall()
            print(f"     Children (Sub-rules/Explanations):")
            for sub in sub_rows:
                print(f"       └─ [{sub['node_type'].upper()}] {sub['node_number']} {sub['title']}")
                # Trace clauses under this sub-rule if they exist
                clause_cursor = conn.execute("""
                SELECT id, node_type, node_number, title 
                FROM document_hierarchy 
                WHERE parent_node_id = ? AND node_type = 'clause'
                """, (sub["id"],))
                clauses = clause_cursor.fetchall()
                for cl in clauses:
                    print(f"           └─ [CLAUSE] {cl['node_number']} {cl['title']}")
        else:
            print("   ❌ IT Rules Rule 3 not found in database.")

    print("\n📢 7. Verifying Government Notification & Cross-References:")
    with get_db_conn() as conn:
        # Get notification
        cursor = conn.execute("SELECT id, title, metadata FROM documents WHERE document_type = 'Notification' LIMIT 1")
        row = cursor.fetchone()
        if row:
            print(f"   Notification Found: '{row['title']}'")
            # Check references from this notification
            refs_cursor = conn.execute("""
            SELECT r.citation_text, r.reference_type, h_tgt.node_number as tgt_num, d_tgt.title as tgt_doc
            FROM cross_references r
            JOIN document_hierarchy h_src ON r.source_node_id = h_src.id
            LEFT JOIN document_hierarchy h_tgt ON r.target_node_id = h_tgt.id
            LEFT JOIN documents d_tgt ON h_tgt.document_id = d_tgt.id
            WHERE h_src.document_id = ?
            """, (row["id"],))
            refs = refs_cursor.fetchall()
            if refs:
                for idx, ref in enumerate(refs, 1):
                    link_status = f"RESOLVED ➔ {ref['tgt_doc']} {ref['tgt_num'] or ''}" if ref['tgt_num'] else "UNRESOLVED"
                    print(f"     [{idx}] Citation: '{ref['citation_text']}' ({ref['reference_type']})")
                    print(f"         Status: {link_status}")
            else:
                print("     ❌ No cross-references found for this notification.")
        else:
            print("   ❌ No Notification records found in database.")

    # ------------------------------------------------------------
    # 5. Semantic Vector Search Verification
    # ------------------------------------------------------------
    print("\n🎯 8. Running Semantic Search Query Verification:")
    embedding_service = get_embedding_service()
    store = get_vector_store()
    
    test_queries = [
        "consequences of breach of contract compensation",
        "basic structure doctrine judicial review power",
        "right to life and personal liberty travel abroad",
        "intermediary due diligence rules 24 hours complaint",
        "misleading information government business"
    ]
    
    for q in test_queries:
        print(f"\n   🔍 Query: '{q}'")
        results = store.search_by_text(q, embedding_service, n_results=2)
        if results["documents"]:
            for i, (doc, meta, dist) in enumerate(zip(results["documents"], results["metadatas"], results["distances"]), 1):
                print(f"     [{i}] Result (dist: {dist:.4f}):")
                print(f"         Source: {meta.get('source')} | Section: {meta.get('section')}")
                print(f"         Title: {meta.get('title')}")
                # Print relational links from SQLite
                node_id = results["ids"][i-1]
                refs = get_node_references(node_id)
                incoming = get_incoming_references(node_id)
                versions = get_node_versions(node_id)
                
                if refs:
                    print(f"         Outbound References: {[r['citation_text'] for r in refs]}")
                if incoming:
                    print(f"         Inbound References (Cited By): {[(r['source_doc_title'] + ' ' + (r['source_number'] or '')) for r in incoming]}")
                if len(versions) > 1:
                    print(f"         Versions available: {len(versions)} versions")
        else:
            print("     ❌ No results returned.")

if __name__ == "__main__":
    verify_kb_v2()
