"""
LegalDocAI - Vector Store (ChromaDB)
Stores and retrieves legal document chunks using ChromaDB.
"""

import sys
from pathlib import Path
import chromadb
from chromadb.config import Settings

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_LEGAL_KB


class LegalVectorStore:
    """
    ChromaDB wrapper for storing and searching legal document embeddings.

    Collections:
      - legal_knowledge_base: Constitution, IPC/BNS, CrPC/BNSS, Evidence/BSA
      - case_documents: User-uploaded case documents (used in Phase 2)
    """

    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        print(f"  [DB] Initializing ChromaDB at: {persist_dir}")
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persist_dir)
        print(f"  [OK] ChromaDB initialized")

    def get_or_create_collection(self, name: str = CHROMA_COLLECTION_LEGAL_KB):
        """Get an existing collection or create a new one."""
        collection = self.client.get_or_create_collection(
            name=name,
            metadata={"description": f"LegalDocAI - {name}"}
        )
        print(f"  [COLLECTION] Collection '{name}': {collection.count()} documents")
        return collection

    def add_chunks(self, chunks: list, embeddings: list, collection_name: str = CHROMA_COLLECTION_LEGAL_KB):
        """
        Add legal chunks with their embeddings to ChromaDB.

        Args:
            chunks: List of LegalChunk objects
            embeddings: List of embedding vectors (matching order with chunks)
            collection_name: ChromaDB collection name
        """
        collection = self.get_or_create_collection(collection_name)

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            # Create a unique ID: source_category_section_index
            source_key = chunk.metadata.get("source", "unknown").replace(" ", "_")[:20]
            section = chunk.metadata.get("article_number", "") or chunk.metadata.get("section_number", "") or str(i)
            chunk_id = f"{source_key}_{section}_{i}"

            ids.append(chunk_id)
            documents.append(chunk.text)

            # ChromaDB metadata must be str, int, float, or bool
            clean_metadata = {}
            for key, value in chunk.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    clean_metadata[key] = value
                else:
                    clean_metadata[key] = str(value)
            metadatas.append(clean_metadata)

        # Add in batches (ChromaDB handles large batches well, but we batch for safety)
        batch_size = 500
        total_added = 0

        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i : i + batch_size]
            batch_docs = documents[i : i + batch_size]
            batch_metas = metadatas[i : i + batch_size]
            batch_embeds = embeddings[i : i + batch_size]

            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas,
                embeddings=batch_embeds,
            )
            total_added += len(batch_ids)

        print(f"  [OK] Added {total_added} chunks to collection '{collection_name}'")
        print(f"  [TOTAL] Total in collection: {collection.count()}")

    def search(self, query_embedding: list, collection_name: str = CHROMA_COLLECTION_LEGAL_KB,
               n_results: int = 5, where: dict = None) -> dict:
        """
        Search for similar chunks using a query embedding.

        Args:
            query_embedding: Embedding vector of the query
            collection_name: Which collection to search
            n_results: Number of results to return
            where: Optional metadata filter (e.g., {"category": "constitution"})

        Returns:
            Dict with 'documents', 'metadatas', 'distances'
        """
        collection = self.get_or_create_collection(collection_name)

        search_params = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
        }

        if where:
            search_params["where"] = where

        results = collection.query(**search_params)

        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
        }

    def search_by_text(self, query_text: str, embedding_service,
                       collection_name: str = CHROMA_COLLECTION_LEGAL_KB,
                       n_results: int = 5, where: dict = None) -> dict:
        """
        High-level search: takes text query, embeds it, searches ChromaDB.

        Args:
            query_text: The search query in plain text
            embedding_service: EmbeddingService instance
            collection_name: Which collection to search
            n_results: Number of results
            where: Optional metadata filter

        Returns:
            Dict with 'documents', 'metadatas', 'distances'
        """
        query_embedding = embedding_service.embed_text(query_text)
        return self.search(query_embedding, collection_name, n_results, where)

    def get_collection_stats(self, collection_name: str = CHROMA_COLLECTION_LEGAL_KB) -> dict:
        """Get statistics about a collection."""
        collection = self.get_or_create_collection(collection_name)
        count = collection.count()

        # Get a sample to show categories
        if count > 0:
            sample = collection.peek(limit=10)
            categories = set()
            sources = set()
            for meta in sample.get("metadatas", []):
                if meta:
                    categories.add(meta.get("category", "unknown"))
                    sources.add(meta.get("source", "unknown"))
        else:
            categories = set()
            sources = set()

        return {
            "collection_name": collection_name,
            "total_chunks": count,
            "categories": list(categories),
            "sources": list(sources),
        }

    def clear_collection(self, collection_name: str = CHROMA_COLLECTION_LEGAL_KB):
        """Delete and recreate a collection (use with caution)."""
        self.client.delete_collection(collection_name)
        print(f"  [CLEARED] Deleted collection: {collection_name}")
        self.get_or_create_collection(collection_name)
        print(f"  [OK] Recreated empty collection: {collection_name}")


# Singleton instance
_vector_store = None


def get_vector_store() -> LegalVectorStore:
    """Get or create the singleton LegalVectorStore instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = LegalVectorStore()
    return _vector_store


if __name__ == "__main__":
    # Quick test
    store = LegalVectorStore()
    stats = store.get_collection_stats()
    print(f"\n  📊 Collection Stats: {stats}")
