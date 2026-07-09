import os
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models.database import update_user_document_status
from app.utils.logging import get_logger
from app.utils.exceptions import EmbeddingError, InvalidDocument
from scripts.embedding_service import get_embedding_service
from scripts.vector_store import get_vector_store

log = get_logger("pdf_processor")

class PDFProcessor:
    """
    Background worker service that parses uploaded legal PDFs page-by-page,
    chunks them with overlap, generates MiniLM vector embeddings, and stores
    them in ChromaDB case_documents collection.
    """
    
    @staticmethod
    def process(doc_id: str, file_path: str, filename: str) -> None:
        """
        Extracts, chunks, embeds, and indexes an uploaded PDF in a background thread.
        Updates SQLite status accordingly.
        """
        log.info(f"Starting background PDF processing for doc_id: {doc_id}, file: {filename}")
        update_user_document_status(doc_id, "processing")
        
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found at: {file_path}")
                
            # 1. Parse PDF text page-by-page
            try:
                doc = fitz.open(str(path))
            except Exception as e:
                raise InvalidDocument(f"Failed to open PDF document: {str(e)}")
                
            total_pages = len(doc)
            log.info(f"Opened PDF successfully. Total pages: {total_pages}")
            
            # Setup splitter
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100
            )
            
            texts = []
            metadatas = []
            ids = []
            chunk_idx = 0
            
            from app.models.database import insert_user_document_chunk
            
            for page_idx in range(total_pages):
                page = doc[page_idx]
                page_text = page.get_text()
                page_num = page_idx + 1
                
                if not page_text.strip():
                    continue
                    
                # Log parsed page text (Step 1)
                log.info(
                    f"Page Text Extraction — DocID: {doc_id} | Page: {page_num} | "
                    f"Length: {len(page_text)} | First 300 chars: {repr(page_text[:300])}"
                )
                
                # Split this page's text
                chunks = splitter.split_text(page_text)
                for c_idx, chunk in enumerate(chunks):
                    contextual_header = f"Document: {filename} | Page: {page_num} | Chunk: {c_idx+1}"
                    contextual_text = f"Context: {contextual_header}\n\n{chunk}"
                    
                    chunk_id = f"{doc_id}_p{page_num}_c{c_idx}_{chunk_idx}"
                    
                    # Log chunk creation (Step 2)
                    log.info(
                        f"Chunk Created — DocID: {doc_id} | ChunkID: {chunk_id} | Page: {page_num} | "
                        f"Length: {len(contextual_text)} | First 300 chars: {repr(contextual_text[:300])}"
                    )
                    
                    # Persist in SQLite chunks table for keyword fallback
                    insert_user_document_chunk(chunk_id, doc_id, page_num, c_idx, contextual_text)
                    
                    texts.append(contextual_text)
                    ids.append(chunk_id)
                    metadatas.append({
                        "law": doc_id,
                        "page": page_num,
                        "document_type": "user_document",
                        "title": filename,
                        "section": f"Page {page_num} (Chunk {c_idx+1})",
                        "source": filename
                    })
                    chunk_idx += 1
            
            doc.close()
            
            if not texts:
                raise InvalidDocument("The uploaded PDF does not contain any readable text.")
                
            log.info(f"Text extraction complete. Total chunks generated: {len(texts)}")
            
            # 2. Generate embeddings
            try:
                embedding_service = get_embedding_service()
                embeddings = embedding_service.embed_batch(texts)
            except Exception as e:
                raise EmbeddingError(f"Failed to generate embeddings for user PDF: {str(e)}")
                
            # 3. Store in ChromaDB 'case_documents' collection
            store = get_vector_store()
            collection = store.get_or_create_collection(name="case_documents")
            
            # Add in batches
            batch_size = 200
            for i in range(0, len(ids), batch_size):
                b_ids = ids[i : i + batch_size]
                b_docs = texts[i : i + batch_size]
                b_metas = metadatas[i : i + batch_size]
                b_embeds = embeddings[i : i + batch_size]
                
                collection.add(
                    ids=b_ids,
                    documents=b_docs,
                    metadatas=b_metas,
                    embeddings=b_embeds
                )
                
            log.info(f"Successfully stored {len(ids)} chunks in ChromaDB case_documents collection.")
            
            # Verify ChromaDB Insert (Step 3)
            try:
                verify_res = collection.get(where={"law": doc_id}, limit=5)
                total_stored = len(verify_res.get("ids", [])) if verify_res else 0
                log.info(f"Verify ChromaDB Insert — DocID: {doc_id} | Total chunks stored in ChromaDB query: {total_stored}")
                if total_stored > 0:
                    log.info(f"Sample stored chunk text: {repr(verify_res['documents'][0][:300])}")
                    log.info(f"Sample stored metadata: {verify_res['metadatas'][0]}")
            except Exception as v_err:
                log.error(f"Failed to run post-insert verification: {v_err}")
            
            # Update SQLite status to processed
            update_user_document_status(doc_id, "processed", total_pages=total_pages, total_chunks=len(ids))
            log.info(f"PDF processing completed successfully for doc_id: {doc_id}")
            
        except Exception as e:
            log.error(f"PDF processing failed for doc_id {doc_id}: {e}", exc_info=True)
            update_user_document_status(doc_id, "failed")
