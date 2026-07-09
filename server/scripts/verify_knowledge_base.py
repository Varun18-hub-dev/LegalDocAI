"""
LegalDocAI - Verify Knowledge Base
Tests the knowledge base by running search queries and checking results.
Run this after build_knowledge_base.py to confirm everything works.

Usage:
  python verify_knowledge_base.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.embedding_service import get_embedding_service
from scripts.vector_store import get_vector_store


def verify():
    """Run test queries against the knowledge base."""

    print("=" * 70)
    print("🔍 LegalDocAI - Knowledge Base Verification")
    print("=" * 70)

    # Initialize services
    embedding_service = get_embedding_service()
    store = get_vector_store()

    # Print stats
    stats = store.get_collection_stats()
    print(f"\n📊 Collection Stats:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Categories: {stats['categories']}")
    print(f"   Sources: {stats['sources']}")

    if stats["total_chunks"] == 0:
        print("\n❌ Knowledge base is empty! Run build_knowledge_base.py first.")
        return

    # --------------------------------------------------------
    # Test Queries
    # --------------------------------------------------------
    test_queries = [
        {
            "query": "right to life and personal liberty",
            "expected": "Article 21",
            "description": "Should find Article 21 of Constitution",
        },
        {
            "query": "freedom of speech and expression",
            "expected": "Article 19",
            "description": "Should find Article 19 of Constitution",
        },
        {
            "query": "right to equality before law",
            "expected": "Article 14",
            "description": "Should find Article 14 of Constitution",
        },
        {
            "query": "punishment for theft",
            "expected": "Section 303",
            "description": "Should find BNS Section 303 (Theft)",
        },
        {
            "query": "murder punishment death sentence",
            "expected": "Section 101",
            "description": "Should find BNS Section 101 (Murder)",
        },
        {
            "query": "bail provisions for accused",
            "expected": "bail",
            "description": "Should find BNSS bail-related sections",
        },
        {
            "query": "evidence admissibility in court",
            "expected": "evidence",
            "description": "Should find BSA evidence-related sections",
        },
    ]

    print("\n" + "-" * 70)
    print("🧪 Running Test Queries")
    print("-" * 70)

    passed = 0
    failed = 0

    for i, test in enumerate(test_queries, 1):
        print(f"\n{'─' * 60}")
        print(f"  Query {i}: \"{test['query']}\"")
        print(f"  Expected: {test['description']}")

        results = store.search_by_text(
            query_text=test["query"],
            embedding_service=embedding_service,
            n_results=3,
        )

        if results["documents"]:
            print(f"  ✅ Found {len(results['documents'])} results:")
            for j, (doc, meta, dist) in enumerate(
                zip(results["documents"], results["metadatas"], results["distances"])
            ):
                source = meta.get("source", "N/A")
                article = meta.get("article_number", "") or meta.get("section_number", "N/A")
                print(f"\n     Result {j+1} (distance: {dist:.4f}):")
                print(f"     Source: {source}")
                print(f"     Article/Section: {article}")
                print(f"     Text: {doc[:200]}...")

            passed += 1
        else:
            print(f"  ❌ No results found!")
            failed += 1

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"📊 Verification Results: {passed}/{passed + failed} queries returned results")
    if failed == 0:
        print("✅ All queries passed! Knowledge base is working correctly.")
    else:
        print(f"⚠️  {failed} queries failed. Check the data pipeline.")
    print("=" * 70)

    # --------------------------------------------------------
    # Interactive mode
    # --------------------------------------------------------
    print("\n💡 Try your own queries (type 'quit' to exit):\n")

    while True:
        query = input("  🔍 Your query: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break

        if not query:
            continue

        results = store.search_by_text(
            query_text=query,
            embedding_service=embedding_service,
            n_results=5,
        )

        if results["documents"]:
            for j, (doc, meta, dist) in enumerate(
                zip(results["documents"], results["metadatas"], results["distances"])
            ):
                source = meta.get("source", "N/A")
                article = meta.get("article_number", "") or meta.get("section_number", "N/A")
                print(f"\n     Result {j+1} (distance: {dist:.4f}):")
                print(f"     Source: {source} | Article/Section: {article}")
                print(f"     Text: {doc[:300]}...")
        else:
            print("  No results found.")

        print()


if __name__ == "__main__":
    verify()
