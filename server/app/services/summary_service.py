from app.models.context import QueryContext
from app.utils.logging import get_logger
from app.utils.exceptions import RetrievalError
from scripts.vector_store import get_vector_store
from app.services.llm_service import LLMService

log = get_logger("summary_service")

class SummaryService:
    """
    Service responsible for sequential (Map-Reduce) summarization of uploaded documents.
    Supports large documents by summarizing chunks and consolidating.
    """
    
    @staticmethod
    def summarize(context: QueryContext) -> str:
        """
        Public contract method to generate document summaries.
        Saves summary in context.llm_response and returns it.
        """
        context.start_stage("document_summary")
        try:
            doc_id = context.document_id
            if not doc_id:
                raise ValueError("Document ID must be set in context.document_id for summarization.")
                
            log.info(f"Retrieving text chunks to summarize document: {doc_id}")
            
            store = get_vector_store()
            collection = store.get_or_create_collection(name="case_documents")
            
            # Fetch all chunks
            res = collection.get(where={"law": doc_id})
            if not res or not res.get("documents"):
                raise RetrievalError(f"No chunks found for document ID: {doc_id}")
                
            # Reconstruct document text sorted by page/id
            chunks = []
            for doc, meta, id_ in zip(res["documents"], res["metadatas"], res["ids"]):
                chunks.append({
                    "text": doc.split("\n\n", 1)[1] if "\n\n" in doc else doc,
                    "page": meta.get("page", 1),
                    "id": id_
                })
            chunks.sort(key=lambda x: (x["page"], x["id"]))
            
            full_text = "\n\n".join([f"--- Page {c['page']} ---\n{c['text']}" for c in chunks])
            log.info(f"Reconstructed full document text ({len(full_text)} chars)")
            
            # Decide summarization strategy based on document length
            # If text is small (< 30,000 chars), summarize directly
            if len(full_text) < 30000:
                summary = SummaryService._generate_direct_summary(context, full_text)
            else:
                summary = SummaryService._generate_map_reduce_summary(context, chunks)
                
            context.llm_response = summary
            return summary
            
        except Exception as e:
            log.error(f"Document summarization failed: {e}", exc_info=True)
            context.errors.append(f"Summarization failed: {str(e)}")
            raise e
        finally:
            context.end_stage("document_summary")

    @staticmethod
    def _generate_direct_summary(context: QueryContext, text: str) -> str:
        """Summarize the entire text in a single LLM call."""
        log.info("Generating direct document summary...")
        prompt = f"""You are an expert legal assistant. Provide a structured executive summary of the document below.

=== DOCUMENT CONTENT ===
{text}
=========================

Instructions:
1. Extract the core purpose and contracting parties.
2. Outline key terms and obligations in bullet points.
3. Identify liability caps, indemnification provisions, and breach consequences.
4. Detail termination conditions and dispute resolution forums.
5. Provide a summary of the governing law.

Executive Summary:"""
        
        context.prompt = prompt
        return LLMService.generate(context)

    @staticmethod
    def _generate_map_reduce_summary(context: QueryContext, chunks: list) -> str:
        """Map-Reduce summary: summarize chunks of pages, then combine."""
        log.info("Generating Map-Reduce document summary...")
        
        # 1. Map Stage: Group pages and summarize them
        log.info("Map Stage: Summarizing page groups...")
        intermediate_summaries = []
        current_batch = []
        current_len = 0
        
        # Helper to process batch
        def process_batch(batch_chunks, idx):
            batch_text = "\n\n".join([f"Page {c['page']}: {c['text']}" for c in batch_chunks])
            batch_prompt = f"""Summarize the following section of a legal document briefly:
            
            {batch_text}
            
            Focus on obligations, dates, and liability terms.
            Summary:"""
            # Create a sub-context to avoid corrupting main timings/logs
            sub_ctx = QueryContext(question="batch_summary")
            sub_ctx.prompt = batch_prompt
            sub_ctx.intent = context.intent
            return LLMService.generate(sub_ctx)
            
        for idx, chunk in enumerate(chunks):
            current_batch.append(chunk)
            current_len += len(chunk["text"])
            
            # Process in ~15,000 char batches
            if current_len > 15000 or idx == len(chunks) - 1:
                batch_sum = process_batch(current_batch, idx)
                intermediate_summaries.append(batch_sum)
                current_batch = []
                current_len = 0
                
        log.info(f"Generated {len(intermediate_summaries)} intermediate summaries.")
        
        # 2. Reduce Stage: Combine intermediate summaries into the final summary
        log.info("Reduce Stage: Consolidating summaries...")
        combined_text = "\n\n".join([f"Section {i+1} Summary:\n{s}" for i, s in enumerate(intermediate_summaries)])
        
        final_prompt = f"""Consolidate the following section summaries of a legal document into a unified, structured executive summary.
        
        === SECTION SUMMARIES ===
        {combined_text}
        =========================
        
        Instructions:
        1. Structure the summary with headers: Purpose, Parties, Key Obligations, Termination & Dispute Resolution.
        2. Keep the output bulleted and highly professional.
        3. Do not include introductory or concluding conversational text.
        
        Consolidated Executive Summary:"""
        
        context.prompt = final_prompt
        return LLMService.generate(context)
