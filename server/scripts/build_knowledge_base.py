"""
LegalDocAI - Build Knowledge Base (Main Pipeline)
Runs the complete Phase 1 pipeline:
  1. Download legal PDFs
  2. Extract text from PDFs
  3. Chunk text into Articles/Sections
  4. Generate embeddings
  5. Store in ChromaDB

Usage:
  python build_knowledge_base.py          # Run full pipeline
  python build_knowledge_base.py --skip-download   # Skip download step
  python build_knowledge_base.py --reset  # Clear DB and rebuild
"""

import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DATA_SOURCES, RAW_DATA_DIR, PROCESSED_DATA_DIR
from scripts.download_sources import download_all
from scripts.pdf_extractor import extract_text_from_pdf, save_extracted_text
from scripts.chunker import chunk_document
from scripts.embedding_service import get_embedding_service
from scripts.vector_store import get_vector_store


def build_knowledge_base(skip_download: bool = False, reset: bool = False):
    """
    Main pipeline: Download → Extract → Chunk → Embed → Store
    """
    start_time = time.time()

    print("=" * 70)
    print("🏛️  LegalDocAI - Knowledge Base Builder")
    print("=" * 70)

    # --------------------------------------------------------
    # Step 0: Reset if requested
    # --------------------------------------------------------
    if reset:
        print("\n🗑️  Resetting vector store...")
        store = get_vector_store()
        store.clear_collection()
        print("  ✅ Vector store cleared")

    # --------------------------------------------------------
    # Step 1: Download PDFs
    # --------------------------------------------------------
    if not skip_download:
        print("\n" + "=" * 70)
        print("📥 STEP 1: Downloading Legal Documents")
        print("=" * 70)
        download_results = download_all()
    else:
        print("\n⏭️  Skipping download (--skip-download flag)")

    # --------------------------------------------------------
    # Step 2: Extract text from PDFs
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("📖 STEP 2: Extracting Text from PDFs")
    print("=" * 70)

    extracted_docs = {}

    for key, source in DATA_SOURCES.items():
        pdf_path = RAW_DATA_DIR / source["filename"]

        if not pdf_path.exists():
            print(f"\n  ⚠️  PDF not found: {source['filename']}")
            print(f"     Please download manually and place in: {RAW_DATA_DIR}")
            continue

        print(f"\n  📄 Processing: {source['name']}")
        doc = extract_text_from_pdf(pdf_path)
        save_extracted_text(doc, PROCESSED_DATA_DIR)
        extracted_docs[key] = doc

    print(f"\n  📊 Extracted {len(extracted_docs)} documents")

    if not extracted_docs:
        print("\n  ❌ No documents extracted! Please ensure PDFs are in the data/raw/ folder.")
        print(f"     Path: {RAW_DATA_DIR}")
        return

    # --------------------------------------------------------
    # Step 3: Chunk documents
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("✂️  STEP 3: Chunking Documents into Articles/Sections")
    print("=" * 70)

    all_chunks = []

    for key, doc in extracted_docs.items():
        source_config = DATA_SOURCES[key]
        chunks = chunk_document(doc.full_text, key, source_config)
        all_chunks.extend(chunks)

    print(f"\n  📊 Total chunks: {len(all_chunks)}")

    if not all_chunks:
        print("\n  ❌ No chunks created! Check the extraction step.")
        return

    # Show sample chunks
    print(f"\n  📋 Sample chunks:")
    for i, chunk in enumerate(all_chunks[:3]):
        print(f"\n  --- Chunk {i+1} ---")
        print(f"  Source: {chunk.metadata.get('source', 'N/A')}")
        print(f"  Section: {chunk.metadata.get('article_number', '') or chunk.metadata.get('section_number', 'N/A')}")
        print(f"  Text: {chunk.text[:150]}...")

    # --------------------------------------------------------
    # Step 4: Generate embeddings
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("🔢 STEP 4: Generating Embeddings (MiniLM)")
    print("=" * 70)

    embedding_service = get_embedding_service()

    # Extract texts for embedding
    texts = [chunk.text for chunk in all_chunks]
    embeddings = embedding_service.embed_batch(texts)

    print(f"\n  📊 Generated {len(embeddings)} embeddings (dimension: {len(embeddings[0])})")

    # --------------------------------------------------------
    # Step 5: Store in ChromaDB
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("🗄️  STEP 5: Storing in ChromaDB")
    print("=" * 70)

    store = get_vector_store()
    store.add_chunks(all_chunks, embeddings)

    # Print final stats
    stats = store.get_collection_stats()
    print(f"\n  📊 Final Stats:")
    print(f"     Total chunks: {stats['total_chunks']}")
    print(f"     Categories: {stats['categories']}")
    print(f"     Sources: {stats['sources']}")

    # --------------------------------------------------------
    # Done!
    # --------------------------------------------------------
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"✅ KNOWLEDGE BASE BUILT SUCCESSFULLY!")
    print(f"   Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"   Total chunks stored: {stats['total_chunks']}")
    print("=" * 70)

    print("\n💡 Next step: Run 'python verify_knowledge_base.py' to test search queries")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the LegalDocAI Knowledge Base")
    parser.add_argument("--skip-download", action="store_true", help="Skip the PDF download step")
    parser.add_argument("--reset", action="store_true", help="Clear existing DB and rebuild from scratch")

    args = parser.parse_args()
    build_knowledge_base(skip_download=args.skip_download, reset=args.reset)
