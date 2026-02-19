"""RAG service using Pinecone with Sentence Transformers for embeddings."""

import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from app.services.cache_service import CacheService
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Embedding model config
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


class RAGService:
    """
    RAG service using Pinecone + Sentence Transformers.
    
    Uses all-MiniLM-L6-v2 (384 dims) for embeddings.
    Per-user data isolation via Pinecone namespaces (user_{user_id}).
    
    Free tier limits:
    - 1 index, 100K vectors, 100 queries/minute
    """
    
    def __init__(
        self,
        api_key: str,
        environment: Optional[str],   # kept for compat, unused in Pinecone v3+
        index_name: str,
        cache: CacheService
    ):
        self.index_name = index_name
        self.cache = cache
        self.index = None
        self.embedding_model = None
        self.embedding_dim = EMBEDDING_DIM

        # Initialize Pinecone client
        try:
            self.pc = Pinecone(api_key=api_key)
        except Exception as e:
            logger.error("pinecone_client_init_failed", error=str(e))
            self.pc = None

        # Load Sentence Transformer model — can be slow on first run
        try:
            logger.info("loading_embedding_model", model=EMBEDDING_MODEL_NAME)
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        except Exception as e:
            logger.error("embedding_model_load_failed", error=str(e))

        # Connect to Pinecone index
        self._initialize_index()

        logger.info(
            "rag_service_initialized",
            index_name=index_name,
            embedding_model=EMBEDDING_MODEL_NAME,
            embedding_dim=EMBEDDING_DIM,
            healthy=self.index is not None,
        )
    
    def _initialize_index(self):
        """Initialize or connect to Pinecone index (non-fatal on failure)."""
        if self.pc is None:
            logger.warning("skipping_index_init_no_client")
            return
        try:
            existing_indexes = self.pc.list_indexes()

            if self.index_name not in [idx.name for idx in existing_indexes]:
                logger.info("creating_pinecone_index", name=self.index_name)
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dim,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )

            self.index = self.pc.Index(self.index_name)
            logger.info("connected_to_index", name=self.index_name)

        except Exception as e:
            # Log and continue — RAG features will be disabled but the server stays up
            logger.error("index_initialization_failed", error=str(e))
            self.index = None
    
    # ──────────────── Embedding ────────────────
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Sentence Transformers (sync)."""
        return self.embedding_model.encode(text).tolist()
    
    def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        return [e.tolist() for e in embeddings]
    
    async def _async_embed(self, text: str) -> List[float]:
        """Async wrapper around sync embedding."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._generate_embedding, text)
    
    async def _async_embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Async wrapper around batch embedding."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._generate_embeddings_batch, texts)
    
    # ──────────────── PDF Processing ────────────────
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
        """Extract text from PDF, page by page."""
        reader = PdfReader(pdf_path)
        pages = []
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({
                    "page_num": i + 1,
                    "text": text,
                    "source": Path(pdf_path).name,
                })
        
        logger.info("pdf_text_extracted", path=pdf_path, pages=len(pages))
        return pages
    
    @staticmethod
    def chunk_text(
        pages: List[Dict],
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> List[Dict]:
        """Split page text into overlapping word-based chunks."""
        chunks = []
        
        for page in pages:
            words = page["text"].split()
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i : i + chunk_size]
                chunk_text = " ".join(chunk_words)
                if chunk_text.strip():
                    chunks.append({
                        "text": chunk_text,
                        "page_num": page["page_num"],
                        "source": page["source"],
                        "chunk_id": len(chunks),
                    })
        
        logger.info("text_chunked", total_chunks=len(chunks))
        return chunks
    
    # ──────────────── Upload ────────────────
    
    async def upload_pdf(
        self,
        pdf_path: str,
        user_id: str,
        doc_id: str,
        original_filename: str,
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Full pipeline: extract PDF → chunk → embed → upsert to Pinecone.
        
        Uses namespace `user_{user_id}` for per-user isolation.
        Returns metadata about the upload.
        """
        namespace = f"user_{user_id}"
        
        # Extract & chunk
        pages = self.extract_text_from_pdf(pdf_path)
        if not pages:
            raise ValueError("No text could be extracted from the PDF.")
        
        chunks = self.chunk_text(pages)
        
        # Embed & upsert in batches
        total_uploaded = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c["text"] for c in batch]
            
            embeddings = await self._async_embed_batch(texts)
            
            vectors = []
            for chunk, embedding in zip(batch, embeddings):
                vector_id = f"{doc_id}_chunk_{chunk['chunk_id']}"
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "text": chunk["text"],
                        "page": chunk["page_num"],
                        "source": original_filename,
                        "doc_id": doc_id,
                        "user_id": user_id,
                        "chunk_id": chunk["chunk_id"],
                    },
                })
            
            self.index.upsert(vectors=vectors, namespace=namespace)
            total_uploaded += len(vectors)
            
            logger.info(
                "batch_upserted",
                batch=i // batch_size + 1,
                vectors=len(vectors),
                namespace=namespace,
            )
        
        result = {
            "doc_id": doc_id,
            "filename": original_filename,
            "pages": len(pages),
            "chunks": len(chunks),
            "vectors_uploaded": total_uploaded,
            "namespace": namespace,
        }
        
        logger.info("pdf_upload_complete", **result)
        return result
    
    # ──────────────── Query ────────────────
    
    async def query(
        self,
        query_text: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        namespace: str = "default",
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone for relevant documents.
        
        Args:
            query_text: Search query
            top_k: Number of results
            filter: Metadata filters
            namespace: Pinecone namespace (use user_{user_id} for per-user)
        """
        # Check cache
        cache_key = f"{query_text}:{top_k}:{filter}:{namespace}"
        cached = await self.cache.get_rag_query(cache_key)
        if cached:
            logger.info("rag_cache_hit", query=query_text[:50])
            return cached
        
        try:
            embedding = await self._async_embed(query_text)
            
            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                filter=filter,
                namespace=namespace,
                include_metadata=True,
            )
            
            documents = []
            for match in results.matches:
                documents.append({
                    "id": match.id,
                    "score": match.score,
                    "text": match.metadata.get("text", ""),
                    "metadata": match.metadata,
                })
            
            # Cache results (7 days)
            await self.cache.cache_rag_query(cache_key, documents, ttl=604800)
            
            logger.info(
                "rag_query_success",
                query=query_text[:50],
                results_count=len(documents),
            )
            return documents
            
        except Exception as e:
            logger.error("rag_query_failed", query=query_text[:50], error=str(e))
            return []
    
    # ──────────────── Document Management ────────────────
    
    async def delete_document_vectors(self, doc_id: str, user_id: str):
        """Delete all vectors belonging to a document from the user's namespace."""
        namespace = f"user_{user_id}"
        try:
            # Use metadata filter to find & delete vectors for this doc
            # Pinecone serverless supports delete by filter
            self.index.delete(
                filter={"doc_id": {"$eq": doc_id}},
                namespace=namespace,
            )
            logger.info("document_vectors_deleted", doc_id=doc_id, namespace=namespace)
        except Exception as e:
            logger.error("delete_vectors_failed", doc_id=doc_id, error=str(e))
            raise
    
    # ──────────────── Stats ────────────────
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "namespaces": stats.namespaces,
            }
        except Exception as e:
            logger.error("get_stats_failed", error=str(e))
            return {}
