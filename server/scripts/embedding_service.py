"""
LegalDocAI - Embedding Service
Generates embeddings using SentenceTransformers (MiniLM) - free, runs locally.
"""

import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import EMBEDDING_MODEL_NAME


class EmbeddingService:
    """
    Generates text embeddings using SentenceTransformers.
    Model: all-MiniLM-L6-v2 (384 dimensions, ~80MB, runs on CPU)
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        print(f"  🧠 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"  ✅ Model loaded! Dimension: {self.dimension}")

    def embed_text(self, text: str) -> list:
        """Generate embedding for a single text string."""
        embedding = self.model.encode(text, show_progress_bar=False)
        return embedding.tolist()

    def embed_batch(self, texts: list, batch_size: int = 64) -> list:
        """
        Generate embeddings for a batch of texts.
        Uses batching for efficiency.

        Args:
            texts: List of text strings
            batch_size: Number of texts to process at once

        Returns:
            List of embedding vectors (each is a list of floats)
        """
        print(f"  🔢 Generating embeddings for {len(texts)} texts...")

        all_embeddings = []

        for i in tqdm(range(0, len(texts), batch_size), desc="  Embedding"):
            batch = texts[i : i + batch_size]
            embeddings = self.model.encode(batch, show_progress_bar=False)
            all_embeddings.extend(embeddings.tolist())

        print(f"  ✅ Generated {len(all_embeddings)} embeddings")
        return all_embeddings


# Singleton instance - reuse across the app
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the singleton EmbeddingService instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


if __name__ == "__main__":
    # Quick test
    service = get_embedding_service()

    test_texts = [
        "Article 21: Right to life and personal liberty",
        "No person shall be deprived of his life",
        "Recipe for chocolate cake",  # should be far from legal texts
    ]

    embeddings = service.embed_batch(test_texts)

    # Calculate similarity
    import numpy as np

    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    print(f"\n  📊 Similarity Test:")
    print(f"  'Article 21' vs 'right to life'  = {cosine_similarity(embeddings[0], embeddings[1]):.4f}  (should be HIGH)")
    print(f"  'Article 21' vs 'chocolate cake'  = {cosine_similarity(embeddings[0], embeddings[2]):.4f}  (should be LOW)")
