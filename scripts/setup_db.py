"""MongoDB database setup script."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.services.db_service import DatabaseService
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def setup_database() -> None:
    """
    Set up MongoDB database with collections and indexes.
    """
    settings = get_settings()
    
    logger.info("starting_database_setup")
    
    try:
        # Initialize database service
        db_service = DatabaseService(
            mongodb_uri=settings.mongodb_uri,
            db_name=settings.mongodb_db_name
        )
        
        # Connect and create indexes
        await db_service.connect()
        
        logger.info("database_setup_complete")
        
        # Test operations
        logger.info("testing_database_operations")
        
        # Test cache
        await db_service.cache_research_data(
            key="test_key",
            data={"test": "data"},
            ttl=3600
        )
        
        cached = await db_service.get_cached_data("test_key")
        assert cached is not None, "Cache test failed"
        
        logger.info("database_tests_passed")
        
        # Cleanup
        await db_service.disconnect()
        
        logger.info("database_setup_successful")
        
    except Exception as e:
        logger.error("database_setup_failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(setup_database())
