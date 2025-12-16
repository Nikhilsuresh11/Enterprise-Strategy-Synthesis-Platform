"""Pinecone index creation and management script."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pinecone import Pinecone, ServerlessSpec
from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_or_verify_index() -> None:
    """
    Create Pinecone index or verify existing index configuration.
    
    For Sentence Transformers (all-MiniLM-L6-v2):
    - Dimension: 384
    - Metric: cosine
    - Cloud: AWS
    - Region: us-east-1
    """
    settings = get_settings()
    
    logger.info("initializing_pinecone_client")
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=settings.pinecone_api_key)
        
        # Check if index exists
        existing_indexes = pc.list_indexes().names()
        
        if settings.pinecone_index_name in existing_indexes:
            logger.info(
                "index_already_exists",
                index_name=settings.pinecone_index_name
            )
            
            # Verify configuration
            index_info = pc.describe_index(settings.pinecone_index_name)
            dimension = index_info.dimension
            
            if dimension != settings.embedding_dimension:
                logger.error(
                    "dimension_mismatch",
                    expected=settings.embedding_dimension,
                    actual=dimension,
                    index_name=settings.pinecone_index_name
                )
                print(f"\n❌ ERROR: Index dimension mismatch!")
                print(f"   Expected: {settings.embedding_dimension} (Sentence Transformers)")
                print(f"   Actual: {dimension}")
                print(f"\n   You need to delete the existing index and recreate it.")
                print(f"   Run: Delete index '{settings.pinecone_index_name}' in Pinecone dashboard")
                print(f"   Then run this script again.\n")
                sys.exit(1)
            
            logger.info(
                "index_verified",
                dimension=dimension,
                metric=index_info.metric
            )
            print(f"\n✅ Index '{settings.pinecone_index_name}' verified successfully!")
            print(f"   Dimension: {dimension}")
            print(f"   Metric: {index_info.metric}")
            print(f"   Ready to use!\n")
            
        else:
            logger.info(
                "creating_new_index",
                index_name=settings.pinecone_index_name,
                dimension=settings.embedding_dimension
            )
            
            # Create new index
            pc.create_index(
                name=settings.pinecone_index_name,
                dimension=settings.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=settings.pinecone_environment
                )
            )
            
            logger.info("index_created", index_name=settings.pinecone_index_name)
            print(f"\n✅ Index '{settings.pinecone_index_name}' created successfully!")
            print(f"   Dimension: {settings.embedding_dimension}")
            print(f"   Metric: cosine")
            print(f"   Cloud: AWS")
            print(f"   Region: {settings.pinecone_environment}")
            print(f"   Ready to use!\n")
        
    except Exception as e:
        logger.error("index_operation_failed", error=str(e))
        print(f"\n❌ ERROR: {str(e)}\n")
        raise


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Pinecone Index Setup - Stratagem AI")
    print("="*60 + "\n")
    
    create_or_verify_index()
