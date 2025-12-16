"""RAG (Retrieval-Augmented Generation) service using Pinecone and Sentence Transformers."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    """
    RAG service for retrieving relevant context from Pinecone vector database.
    
    Uses Sentence Transformers for FREE local embeddings.
    """
    
    def __init__(
        self,
        api_key: str,
        environment: str,
        index_name: str,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> None:
        """
        Initialize RAG service.
        
        Args:
            api_key: Pinecone API key
            environment: Pinecone environment/region
            index_name: Pinecone index name
            embedding_model: Sentence Transformers model name
        """
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.embedding_model_name = embedding_model
        
        # Initialize Sentence Transformers model (runs locally, FREE)
        logger.info("loading_embedding_model", model=embedding_model)
        self.embedding_model = SentenceTransformer(embedding_model)
        
        self.pc = None
        self.index = None
        self._initialized = False
        
        logger.info("rag_service_initialized", index=index_name)
    
    async def connect(self) -> None:
        """Connect to Pinecone and initialize index."""
        try:
            logger.info("connecting_to_pinecone")
            
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=self.api_key)
            
            # Get index
            self.index = self.pc.Index(self.index_name)
            
            # Verify connection
            stats = self.index.describe_index_stats()
            logger.info(
                "pinecone_connected",
                total_vectors=stats.get('total_vector_count', 0)
            )
            
            self._initialized = True
            
        except Exception as e:
            logger.error("pinecone_connection_failed", error=str(e))
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Sentence Transformers.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector (384 dimensions)
        """
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def chunk_document(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for period, question mark, or exclamation
                for char in ['. ', '? ', '! ', '\n\n']:
                    last_break = text[start:end].rfind(char)
                    if last_break != -1:
                        end = start + last_break + len(char)
                        break
            
            chunks.append(text[start:end].strip())
            start = end - chunk_overlap
        
        return chunks
    
    async def upsert_documents(
        self,
        documents: List[Dict[str, Any]],
        namespace: str = "default"
    ) -> Dict[str, int]:
        """
        Chunk documents, generate embeddings, and upsert to Pinecone.
        
        Args:
            documents: List of documents with 'text' and 'metadata' keys
            namespace: Pinecone namespace
            
        Returns:
            Dictionary with inserted and failed counts
        """
        if not self._initialized:
            raise RuntimeError("RAG service not connected. Call connect() first.")
        
        logger.info(
            "upserting_documents",
            count=len(documents),
            namespace=namespace
        )
        
        inserted = 0
        failed = 0
        vectors = []
        
        try:
            for doc_idx, doc in enumerate(documents):
                try:
                    text = doc.get('text', '')
                    metadata = doc.get('metadata', {})
                    
                    # Chunk document
                    chunks = self.chunk_document(text)
                    
                    # Generate embeddings for each chunk
                    for chunk_idx, chunk in enumerate(chunks):
                        # Generate embedding
                        embedding = self._generate_embedding(chunk)
                        
                        # Create unique ID
                        vector_id = f"{namespace}_{doc_idx}_{chunk_idx}"
                        
                        # Add chunk text to metadata
                        chunk_metadata = {
                            **metadata,
                            'text': chunk,
                            'chunk_index': chunk_idx,
                            'total_chunks': len(chunks)
                        }
                        
                        vectors.append({
                            'id': vector_id,
                            'values': embedding,
                            'metadata': chunk_metadata
                        })
                    
                    inserted += 1
                    
                except Exception as e:
                    logger.error("document_processing_failed", doc_idx=doc_idx, error=str(e))
                    failed += 1
            
            # Batch upsert to Pinecone
            if vectors:
                self.index.upsert(vectors=vectors, namespace=namespace)
                logger.info(
                    "vectors_upserted",
                    count=len(vectors),
                    namespace=namespace
                )
            
            return {"inserted": inserted, "failed": failed}
            
        except Exception as e:
            logger.error("upsert_failed", error=str(e))
            raise
    
    async def semantic_search(
        self,
        query: str,
        namespace: str = "default",
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        
        Args:
            query: Search query
            namespace: Pinecone namespace
            top_k: Number of results
            filters: Optional metadata filters
            
        Returns:
            List of results with id, score, metadata, text
        """
        if not self._initialized:
            raise RuntimeError("RAG service not connected. Call connect() first.")
        
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Search Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=namespace,
                filter=filters,
                include_metadata=True
            )
            
            # Format results
            formatted_results = []
            for match in results.get('matches', []):
                formatted_results.append({
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match.get('metadata', {}),
                    'text': match.get('metadata', {}).get('text', '')
                })
            
            logger.debug(
                "semantic_search_complete",
                query=query[:50],
                results_count=len(formatted_results)
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error("semantic_search_failed", error=str(e))
            raise
    
    async def hybrid_search(
        self,
        query: str,
        date_range: Optional[tuple] = None,
        source_types: Optional[List[str]] = None,
        industry: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Combine semantic search with metadata filtering.
        
        Args:
            query: Search query
            date_range: Optional (start_date, end_date) tuple
            source_types: Optional list of source types to filter
            industry: Optional industry filter
            top_k: Number of results
            
        Returns:
            List of filtered results
        """
        # Build metadata filter
        filters = {}
        
        if source_types:
            filters['source_type'] = {'$in': source_types}
        
        if industry:
            filters['industry'] = industry
        
        if date_range:
            start_date, end_date = date_range
            filters['date'] = {
                '$gte': start_date,
                '$lte': end_date
            }
        
        # Perform search with filters
        return await self.semantic_search(
            query=query,
            top_k=top_k,
            filters=filters if filters else None
        )
    
    async def get_relevant_context(
        self,
        query: str,
        context_type: str,
        top_k: int = 5
    ) -> str:
        """
        Retrieve formatted context for agents.
        
        Args:
            query: Search query
            context_type: Type of context (case_study, financial, news, regulatory)
            top_k: Number of results
            
        Returns:
            Formatted context string with citations
        """
        # Map context type to namespace
        namespace_map = {
            'case_study': 'case_studies',
            'financial': 'financial_templates',
            'news': 'news',
            'regulatory': 'regulatory',
            'industry': 'industry_reports'
        }
        
        namespace = namespace_map.get(context_type, 'default')
        
        # Search
        results = await self.semantic_search(
            query=query,
            namespace=namespace,
            top_k=top_k
        )
        
        # Format context
        if not results:
            return "No relevant context found."
        
        context_parts = []
        for idx, result in enumerate(results, 1):
            metadata = result['metadata']
            text = result['text']
            score = result['score']
            
            source = metadata.get('source', 'Unknown')
            date = metadata.get('date', 'N/A')
            
            context_parts.append(
                f"[{idx}] {text}\n"
                f"    Source: {source} | Date: {date} | Relevance: {score:.2f}\n"
            )
        
        return "\n".join(context_parts)
    
    async def ingest_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        namespace: str = "default"
    ) -> None:
        """
        Ingest a single document (convenience method).
        
        Args:
            text: Document text
            metadata: Document metadata
            namespace: Pinecone namespace
        """
        documents = [{
            'text': text,
            'metadata': metadata
        }]
        
        await self.upsert_documents(documents, namespace=namespace)
