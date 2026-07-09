import sys
import time
import json
import argparse
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DATA_SOURCES, RAW_DATA_DIR, PROCESSED_DATA_DIR
from app.models.database import init_db, clear_db, get_db_conn, insert_hierarchy_node
from data.scrapers.indiacode import download_all_acts, ACT_URLS
from data.scrapers.aws_sc_judgments import load_or_create_sc_judgments
from app.services.parser_service import parse_act_to_db, parse_judgment_to_db, parse_notification_to_db
from app.services.reference_service import extract_and_link_references
from scripts.pdf_extractor import extract_text_from_pdf, save_extracted_text
from scripts.embedding_service import get_embedding_service
from scripts.vector_store import get_vector_store

def build_knowledge_base_v2(reset=False):
    """Orchestrator for the Phase 2 production-grade knowledge base builder."""
    start_time = time.time()
    
    print("=" * 70)
    print("🏛️  LegalDocAI - Knowledge Base Builder v2.0")
    print("=" * 70)
    
    # ------------------------------------------------------------
    # Step 0: Initialize database
    # ------------------------------------------------------------
    if reset:
        print("\n🗑️  Resetting database and vector store...")
        clear_db()
        store = get_vector_store()
        store.clear_collection()
        print("  ✅ Database and vector store cleared")
    else:
        init_db()

    # ------------------------------------------------------------
    # Step 1: Download & Ingest Scrapers
    # ------------------------------------------------------------
    print("\n" + "=" * 70)
    print("📥 STEP 1: Running Scrapers and Ingestion")
    print("=" * 70)
    
    # Load SC judgments
    sc_json_path = load_or_create_sc_judgments()
    
    # Download additional acts
    downloaded_acts = download_all_acts()

    # ------------------------------------------------------------
    # Step 2: PDF Text Extraction for Acts
    # ------------------------------------------------------------
    print("\n" + "=" * 70)
    print("📖 STEP 2: Extracting Text from Act PDFs")
    print("=" * 70)
    
    extracted_texts = {}
    
    # Extract core docs (Constitution, BNS, BNSS, BSA)
    for key, source in DATA_SOURCES.items():
        pdf_path = RAW_DATA_DIR / source["filename"]
        txt_path = PROCESSED_DATA_DIR / f"{pdf_path.stem}.txt"
        
        if txt_path.exists():
            print(f"  📄 Text already extracted for core doc: {source['name']}")
            extracted_texts[key] = txt_path.read_text(encoding="utf-8")
        elif pdf_path.exists():
            print(f"  📖 Extracting core: {source['name']}")
            doc = extract_text_from_pdf(pdf_path)
            save_extracted_text(doc, PROCESSED_DATA_DIR)
            extracted_texts[key] = doc.full_text
        else:
            print(f"  ⚠️  Core PDF not found: {source['filename']}")
            
    # Extract downloaded acts
    for key, act_info in ACT_URLS.items():
        pdf_path = RAW_DATA_DIR / act_info["filename"]
        txt_path = PROCESSED_DATA_DIR / f"{pdf_path.stem}.txt"
        
        # If it was fallback downloaded as .txt
        mock_txt_path = RAW_DATA_DIR / f"{pdf_path.stem}.txt"
        
        if mock_txt_path.exists():
            print(f"  📄 Ingesting mock text file for Act: {act_info['name']}")
            extracted_texts[key] = mock_txt_path.read_text(encoding="utf-8")
        elif txt_path.exists():
            print(f"  📄 Text already extracted for Act: {act_info['name']}")
            extracted_texts[key] = txt_path.read_text(encoding="utf-8")
        elif pdf_path.exists():
            print(f"  📖 Extracting PDF: {act_info['name']}")
            doc = extract_text_from_pdf(pdf_path)
            save_extracted_text(doc, PROCESSED_DATA_DIR)
            extracted_texts[key] = doc.full_text
        else:
            print(f"  ⚠️  Act PDF/Text not found: {act_info['filename']}")
            
    # Ingest IT Rules 2021 mock file if exists
    rules_mock_path = RAW_DATA_DIR / "it_rules_2021.txt"
    if rules_mock_path.exists():
        print(f"  📄 Ingesting mock text file for Rules: IT Rules 2021")
        extracted_texts["it_rules_2021"] = rules_mock_path.read_text(encoding="utf-8")

    # ------------------------------------------------------------
    # Step 3: Hierarchical Parsing into SQLite
    # ------------------------------------------------------------
    print("\n" + "=" * 70)
    print("✂️  STEP 3: Hierarchical Parsing into SQLite")
    print("=" * 70)
    
    # Ingest core acts
    for key in ["constitution", "bns", "bnss", "bsa"]:
        if key in extracted_texts:
            name = DATA_SOURCES[key]["name"]
            cat = DATA_SOURCES[key]["category"]
            parse_act_to_db(key, name, extracted_texts[key], cat)
            
    # Ingest downloaded acts
    for key in ACT_URLS:
        if key in extracted_texts:
            name = ACT_URLS[key]["name"]
            cat = ACT_URLS[key]["category"]
            parse_act_to_db(key, name, extracted_texts[key], cat)

    # Ingest judgments
    if sc_json_path.exists():
        with open(sc_json_path, "r", encoding="utf-8") as f:
            judgments = json.load(f)
            for j in judgments:
                parse_judgment_to_db(j)

    # Ingest Rules
    if "it_rules_2021" in extracted_texts:
        parse_act_to_db("it_rules_2021", "Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021", extracted_texts["it_rules_2021"], "rules")

    # Ingest Notifications
    notification_json_path = RAW_DATA_DIR / "it_notification_2023.json"
    if notification_json_path.exists():
        with open(notification_json_path, "r", encoding="utf-8") as f:
            notif = json.load(f)
            parse_notification_to_db(notif)

    # ------------------------------------------------------------
    # Step 4: Extract and Link Cross-References
    # ------------------------------------------------------------
    extract_and_link_references()

    # ------------------------------------------------------------
    # Step 5: Generate Embeddings and Store in ChromaDB
    # ------------------------------------------------------------
    print("\n" + "=" * 70)
    print("🔢 STEP 5: Embedding & Indexing in ChromaDB")
    print("=" * 70)
    
    # Query all nodes from SQLite that have text content
    # We want to index sections, articles, subsections, explanations, provisos, illustrations
    # We exclude Parts and Chapters containers since they don't contain descriptive law text itself
    nodes_to_index = []
    with get_db_conn() as conn:
        cursor = conn.execute("""
        SELECT h.id, h.node_type, h.node_number, h.title, h.text_content, h.parent_node_id, h.document_id,
               d.title as doc_title, d.year as doc_year
        FROM document_hierarchy h
        JOIN documents d ON h.document_id = d.id
        WHERE h.node_type NOT IN ('part', 'chapter', 'schedule')
        """)
        nodes_to_index = [dict(row) for row in cursor.fetchall()]
        
    print(f"  Preparing to embed {len(nodes_to_index)} nodes...")
    
    # Format texts for embeddings, prefixing parents for rich context
    texts = []
    chroma_metadatas = []
    chroma_ids = []
    
    # Cache parent chapter/part titles to speed up lookups
    parent_cache = {}
    
    def get_parent_prefix(parent_id):
        if not parent_id:
            return ""
        if parent_id in parent_cache:
            return parent_cache[parent_id]
            
        with get_db_conn() as conn:
            cursor = conn.execute("SELECT node_number, title, parent_node_id FROM document_hierarchy WHERE id = ?", (parent_id,))
            row = cursor.fetchone()
            if row:
                prefix = f"{row['node_number'] or ''} {row['title'] or ''}".strip()
                # Check for higher parent
                higher_prefix = get_parent_prefix(row['parent_node_id'])
                full_prefix = f"{higher_prefix} > {prefix}" if higher_prefix else prefix
                parent_cache[parent_id] = full_prefix
                return full_prefix
        return ""

    for node in nodes_to_index:
        doc_title = node["doc_title"]
        node_num = node["node_number"] or ""
        node_title = node["title"] or ""
        parent_prefix = get_parent_prefix(node["parent_node_id"])
        
        # Build contextual text
        context_header = f"{doc_title} > {parent_prefix} > {node_num} {node_title}".strip()
        contextual_text = f"Context: {context_header}\n\n{node['text_content']}"
        
        texts.append(contextual_text)
        chroma_ids.append(node["id"])
        
        # Metadata dictionary
        chroma_metadatas.append({
            "document_type": node["node_type"],
            "law": node["document_id"],
            "section": node_num,
            "title": node_title,
            "year": str(node["doc_year"] or ""),
            "jurisdiction": "India",
            "source": doc_title,
            "language": "English"
        })

    if texts:
        # Load local embedding model
        embedding_service = get_embedding_service()
        embeddings = embedding_service.embed_batch(texts)
        
        print(f"  🧠 Generated {len(embeddings)} embeddings.")
        
        # Add to ChromaDB
        store = get_vector_store()
        collection = store.get_or_create_collection()
        
        # Add in batches
        batch_size = 300
        for i in range(0, len(chroma_ids), batch_size):
            b_ids = chroma_ids[i : i + batch_size]
            b_docs = texts[i : i + batch_size]
            b_metas = chroma_metadatas[i : i + batch_size]
            b_embeds = embeddings[i : i + batch_size]
            
            collection.add(
                ids=b_ids,
                documents=b_docs,
                metadatas=b_metas,
                embeddings=b_embeds
            )
            
            # Update SQLite document_hierarchy table with chroma_id links
            with get_db_conn() as conn:
                for idx_id in b_ids:
                    conn.execute("UPDATE document_hierarchy SET chroma_id = ? WHERE id = ?", (idx_id, idx_id))
                    
        print(f"  ✅ Indexed {len(chroma_ids)} nodes in ChromaDB.")
        
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("✅ KNOWLEDGE BASE BUILD COMPLETED SUCCESSFULLY!")
    print(f"   Total elapsed time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Knowledge Base v2")
    parser.add_argument("--reset", action="store_true", help="Reset database and rebuild")
    args = parser.parse_args()
    
    build_knowledge_base_v2(reset=args.reset)
