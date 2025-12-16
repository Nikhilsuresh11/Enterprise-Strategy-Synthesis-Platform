"""
Quick test script to verify knowledge base quality.

Tests RAG retrieval with sample queries.
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag_service import RAGService
from app.config import get_settings


async def test_rag_quality():
    """Test RAG retrieval quality."""
    settings = get_settings()
    
    rag = RAGService(
        api_key=settings.pinecone_api_key,
        environment=settings.pinecone_environment,
        index_name=settings.pinecone_index_name
    )
    
    await rag.connect()
    
    # Test queries
    queries = [
        "market entry strategy for India",
        "DCF valuation methodology",
        "FDI regulations in India",
        "unit economics for SaaS business",
        "competitive analysis framework"
    ]
    
    print("\n" + "="*80)
    print("RAG QUALITY TEST")
    print("="*80 + "\n")
    
    # Check index stats
    stats = rag.index.describe_index_stats()
    print(f"📊 Index Stats:")
    print(f"   Total vectors: {stats.get('total_vector_count', 0)}")
    print(f"   Dimensions: {stats.get('dimension', 0)}")
    print("\n")
    
    # Test queries
    for query in queries:
        print(f"🔍 Query: {query}")
        results = await rag.semantic_search(query, namespace="case_studies", top_k=3)
        
        if results:
            print(f"   ✓ Found {len(results)} results")
            for i, result in enumerate(results, 1):
                metadata = result.get('metadata', {})
                score = result.get('score', 0)
                source = metadata.get('source', 'Unknown')
                print(f"   {i}. {source} (score: {score:.3f})")
        else:
            print("   ✗ No results found")
        
        print()
    
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_rag_quality())
