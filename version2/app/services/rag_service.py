"""Dummy RAG service to bypass heavy dependencies for deployment."""

from typing import List, Dict, Any, Optional

from app.services.cache_service import CacheService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    """
    Dummy RAG service that bypasses Pinecone and PyTorch memory issues.
    Returns empty context so the rest of the application can run.
    """
    
    def __init__(
        self,
        api_key: str,
        environment: Optional[str],
        index_name: str,
        cache: CacheService
    ):
        self.index_name = index_name
        self.cache = cache
        logger.info("dummy_rag_service_initialized")
    
    async def query(
        self, 
        query_text: str, 
        top_k: int = 5, 
        filter: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return empty results safely."""
        logger.info("dummy_rag_query_called", query=query_text)
        return []
    
    async def store_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """Dummy store."""
        return "dummy_id"
        
    async def process_pdf(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        company_name: str,
        document_type: str = "custom"
    ) -> Dict[str, Any]:
        """Dummy process PDF."""
        return {"status": "success", "chunks_stored": 0}
