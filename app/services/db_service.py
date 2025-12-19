"""MongoDB database service for persistent storage."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseService:
    """
    MongoDB database service for Stratagem AI.
    
    Manages all database operations including analysis sessions,
    research caching, and agent execution logs.
    """
    
    def __init__(self, mongodb_uri: str, db_name: str) -> None:
        """
        Initialize database service.
        
        Args:
            mongodb_uri: MongoDB connection URI
            db_name: Database name
        """
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.mongodb_uri = mongodb_uri
        self.db_name = db_name
        self._initialized = False
    
    async def connect(self) -> None:
        """Establish database connection and create indexes."""
        try:
            logger.info("connecting_to_mongodb", uri=self.mongodb_uri)
            
            self.client = AsyncIOMotorClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50
            )
            self.db = self.client[self.db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Create indexes
            await self._create_indexes()
            
            self._initialized = True
            logger.info("mongodb_connected", database=self.db_name)
            
        except PyMongoError as e:
            logger.error("mongodb_connection_failed", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("mongodb_disconnected")
    
    async def _create_indexes(self) -> None:
        """Create database indexes for optimal query performance."""
        if self.db is None:
            return
        
        # Analysis sessions indexes
        await self.db.analysis_sessions.create_indexes([
            IndexModel([("job_id", ASCENDING)], unique=True),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("status", ASCENDING)]),
        ])
        
        # Research cache indexes
        await self.db.research_cache.create_indexes([
            IndexModel([("key", ASCENDING)], unique=True),
            IndexModel([("expires_at", ASCENDING)]),
        ])
        
        # Agent logs indexes
        await self.db.agent_logs.create_indexes([
            IndexModel([("agent_name", ASCENDING), ("timestamp", DESCENDING)]),
            IndexModel([("job_id", ASCENDING)]),
        ])
        
        # Users indexes
        await self.db.users.create_indexes([
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("created_at", DESCENDING)]),
        ])
        
        logger.info("database_indexes_created")
    
    async def save_analysis_session(self, session_data: Dict[str, Any]) -> str:
        """
        Save a new analysis session.
        
        Args:
            session_data: Session data to save
            
        Returns:
            Generated job_id
            
        Raises:
            PyMongoError: If database operation fails
        """
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        job_id = str(uuid.uuid4())
        
        document = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "completed_at": None,
            "request": session_data.get("request", {}),
            "result_urls": None,
            "error_message": None,
            "metadata": session_data.get("metadata", {}),
        }
        
        try:
            await self.db.analysis_sessions.insert_one(document)
            logger.info("analysis_session_created", job_id=job_id)
            return job_id
        except DuplicateKeyError:
            logger.error("duplicate_job_id", job_id=job_id)
            raise
        except PyMongoError as e:
            logger.error("save_session_failed", error=str(e))
            raise
    
    async def get_analysis_session(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an analysis session by job_id.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Session data or None if not found
        """
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        try:
            session = await self.db.analysis_sessions.find_one({"job_id": job_id})
            if session:
                # Remove MongoDB _id field
                session.pop("_id", None)
            return session
        except PyMongoError as e:
            logger.error("get_session_failed", job_id=job_id, error=str(e))
            raise
    
    async def update_session_status(
        self,
        job_id: str,
        status: str,
        progress: int,
        result_urls: Optional[Dict[str, str]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update analysis session status and progress.
        
        Args:
            job_id: Job identifier
            status: New status (queued, processing, completed, failed)
            progress: Progress percentage (0-100)
            result_urls: Optional URLs to generated outputs
            error_message: Optional error message if failed
        """
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        update_data: Dict[str, Any] = {
            "status": status,
            "progress": progress,
            "updated_at": datetime.utcnow(),
        }
        
        if status in ["completed", "failed"]:
            update_data["completed_at"] = datetime.utcnow()
        
        if result_urls:
            update_data["result_urls"] = result_urls
        
        if error_message:
            update_data["error_message"] = error_message
        
        try:
            await self.db.analysis_sessions.update_one(
                {"job_id": job_id},
                {"$set": update_data}
            )
            logger.info(
                "session_status_updated",
                job_id=job_id,
                status=status,
                progress=progress
            )
        except PyMongoError as e:
            logger.error("update_status_failed", job_id=job_id, error=str(e))
            raise
    
    async def update_session_with_results(
        self,
        job_id: str,
        final_state: Dict[str, Any],
        output_paths: Dict[str, str]
    ) -> None:
        """
        Update session with final results.
        
        Args:
            job_id: Job identifier
            final_state: Final state from orchestrator
            output_paths: Paths to generated files
        """
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        update_data = {
            "synthesis": final_state.get("synthesis", {}),
            "slides": final_state.get("slides", []),
            "output_paths": output_paths,
            "metadata": final_state.get("metadata", {}),
            "updated_at": datetime.utcnow()
        }
        
        try:
            await self.db.analysis_sessions.update_one(
                {"job_id": job_id},
                {"$set": update_data}
            )
            logger.info("session_results_updated", job_id=job_id)
        except PyMongoError as e:
            logger.error("update_results_failed", job_id=job_id, error=str(e))
            raise
    
    async def cache_research_data(
        self,
        key: str,
        data: Dict[str, Any],
        ttl: int = 86400
    ) -> None:
        """
        Cache research data with TTL.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (default: 24 hours)
        """
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        document = {
            "key": key,
            "data": data,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
        }
        
        try:
            await self.db.research_cache.update_one(
                {"key": key},
                {"$set": document},
                upsert=True
            )
            logger.debug("research_data_cached", key=key, ttl=ttl)
        except PyMongoError as e:
            logger.error("cache_data_failed", key=key, error=str(e))
            raise
    
    async def get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached research data.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found or expired
        """
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        try:
            cached = await self.db.research_cache.find_one({
                "key": key,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if cached:
                logger.debug("cache_hit", key=key)
                return cached.get("data")
            
            logger.debug("cache_miss", key=key)
            return None
        except PyMongoError as e:
            logger.error("get_cached_data_failed", key=key, error=str(e))
            raise
    
    async def save_agent_log(
        self,
        agent_name: str,
        execution_time: float,
        success: bool,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Save agent execution log.
        
        Args:
            agent_name: Name of the agent
            execution_time: Execution time in seconds
            success: Whether execution was successful
            metadata: Additional metadata (job_id, errors, etc.)
        """
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        document = {
            "agent_name": agent_name,
            "execution_time": execution_time,
            "success": success,
            "timestamp": datetime.utcnow(),
            "metadata": metadata,
        }
        
        try:
            await self.db.agent_logs.insert_one(document)
            logger.debug(
                "agent_log_saved",
                agent_name=agent_name,
                execution_time=execution_time,
                success=success
            )
        except PyMongoError as e:
            logger.error("save_agent_log_failed", agent_name=agent_name, error=str(e))
            # Don't raise - logging failures shouldn't break the workflow
    
    async def get_agent_logs(
        self,
        agent_name: Optional[str] = None,
        job_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve agent execution logs.
        
        Args:
            agent_name: Optional filter by agent name
            job_id: Optional filter by job_id
            limit: Maximum number of logs to return
            
        Returns:
            List of agent logs
        """
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        query: Dict[str, Any] = {}
        if agent_name:
            query["agent_name"] = agent_name
        if job_id:
            query["metadata.job_id"] = job_id
        
        try:
            cursor = self.db.agent_logs.find(query).sort("timestamp", DESCENDING).limit(limit)
            logs = await cursor.to_list(length=limit)
            
            # Remove MongoDB _id field
            for log in logs:
                log.pop("_id", None)
            
            return logs
        except PyMongoError as e:
            logger.error("get_agent_logs_failed", error=str(e))
            raise
    
    async def cleanup_expired_cache(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of deleted entries
        """
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        try:
            result = await self.db.research_cache.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            deleted_count = result.deleted_count
            
            if deleted_count > 0:
                logger.info("expired_cache_cleaned", count=deleted_count)
            
            return deleted_count
        except PyMongoError as e:
            logger.error("cleanup_cache_failed", error=str(e))
            raise
    
    # User Management Methods
    
    async def create_user(
        self,
        email: str,
        password_hash: str
    ) -> str:
        """
        Create a new user.
        
        Args:
            email: User email address
            password_hash: Hashed password
            
        Returns:
            User email
            
        Raises:
            DuplicateKeyError: If email already exists
            PyMongoError: If database operation fails
        """
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        document = {
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "last_login": None,
        }
        
        try:
            await self.db.users.insert_one(document)
            logger.info("user_created", email=email)
            return email
        except DuplicateKeyError:
            logger.error("duplicate_email", email=email)
            raise
        except PyMongoError as e:
            logger.error("create_user_failed", error=str(e))
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by email.
        
        Args:
            email: User email address
            
        Returns:
            User data or None if not found
        """
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        try:
            user = await self.db.users.find_one({"email": email})
            if user:
                # Remove MongoDB _id field
                user.pop("_id", None)
            return user
        except PyMongoError as e:
            logger.error("get_user_failed", email=email, error=str(e))
            raise
    
    async def update_last_login(self, email: str) -> None:
        """
        Update user's last login timestamp.
        
        Args:
            email: User email address
        """
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        try:
            await self.db.users.update_one(
                {"email": email},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            logger.debug("last_login_updated", email=email)
        except PyMongoError as e:
            logger.error("update_last_login_failed", email=email, error=str(e))
            raise
