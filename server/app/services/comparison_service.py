from app.models.context import QueryContext
from app.utils.logging import get_logger
from app.utils.exceptions import RetrievalError
from scripts.vector_store import get_vector_store
from app.services.llm_service import LLMService

log = get_logger("comparison_service")

class ComparisonService:
    """
    Service responsible for retrieving chunks for two user-uploaded documents,
    sorting and aligning them, and invoking Gemini to generate a comparison report.
    """
    
    @staticmethod
    def compare(context: QueryContext) -> str:
        """
        Public contract method to compare two documents.
        Saves result in context.llm_response and returns it.
        The context.metadata should contain 'doc_id_1' and 'doc_id_2'.
        """
        context.start_stage("document_comparison")
        try:
            doc_id_1 = context.metadata.get("doc_id_1")
            doc_id_2 = context.metadata.get("doc_id_2")
            
            if not doc_id_1 or not doc_id_2:
                raise ValueError("Both 'doc_id_1' and 'doc_id_2' must be set in context.metadata for comparison.")
                
            log.info(f"Retrieving text chunks for document comparison: {doc_id_1} vs {doc_id_2}")
            
            store = get_vector_store()
            collection = store.get_or_create_collection(name="case_documents")
            
            # Fetch all chunks for Doc 1
            res_1 = collection.get(where={"law": doc_id_1})
            # Fetch all chunks for Doc 2
            res_2 = collection.get(where={"law": doc_id_2})
            
            if not res_1 or not res_1.get("documents"):
                raise RetrievalError(f"No chunks found for document ID: {doc_id_1}")
            if not res_2 or not res_2.get("documents"):
                raise RetrievalError(f"No chunks found for document ID: {doc_id_2}")
                
            # Align and reconstruct texts
            text_1 = ComparisonService._reconstruct_document(res_1)
            text_2 = ComparisonService._reconstruct_document(res_2)
            
            log.info(f"Reconstructed doc 1 ({len(text_1)} chars) and doc 2 ({len(text_2)} chars)")
            
            # Build comparison prompt
            prompt = f"""You are a professional contract auditor.
Compare the following two legal documents. Align similar clauses and identify additions, removals, and modifications.

=== DOCUMENT 1 ===
{text_1[:15000]}  # Safeguard limit

=== DOCUMENT 2 ===
{text_2[:15000]}  # Safeguard limit

Instructions:
1. Align similar clauses (e.g. Indemnification, Term, Termination, Liability, IP Rights).
2. Detail additions, deletions, and wording revisions.
3. Assess the legal risk impact of the changes (who benefits from the revision).
4. Summarize the key differences in a structured, comparative report.

Comparison Report:"""

            context.prompt = prompt
            
            # Generate comparison using LLMService
            response = LLMService.generate(context)
            context.llm_response = response
            return response
            
        except Exception as e:
            log.error(f"Document comparison failed: {e}", exc_info=True)
            context.errors.append(f"Comparison failed: {str(e)}")
            raise e
        finally:
            context.end_stage("document_comparison")

    @staticmethod
    def _reconstruct_document(chroma_res: dict) -> str:
        """Helper to reconstruct full text from retrieved ChromaDB chunks sorted by page/id."""
        chunks = []
        for doc, meta, id_ in zip(chroma_res["documents"], chroma_res["metadatas"], chroma_res["ids"]):
            chunks.append({
                "text": doc,
                "page": meta.get("page", 1),
                "id": id_
            })
        # Sort chunks by page number and then by ID order
        chunks.sort(key=lambda x: (x["page"], x["id"]))
        
        # Strip contextual headers if needed, or join text directly
        reconstructed = []
        for c in chunks:
            # Extract actual text from contextual prefix if possible
            txt = c["text"]
            if "\n\n" in txt:
                # Remove 'Context: ...' header
                txt = txt.split("\n\n", 1)[1]
            reconstructed.append(f"--- PAGE {c['page']} ---\n{txt}")
            
        return "\n\n".join(reconstructed)
