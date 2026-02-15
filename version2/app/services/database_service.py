"""Database service for persistent storage of users, chat sessions, and analyses."""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import io

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseService:
    """
    MongoDB service for persistent storage.
    
    Collections:
    - users: User accounts
    - chat_sessions: Chat conversations with messages
    - analyses: Completed analysis results
    """
    
    def __init__(self, mongo_uri: str, database: str = "stratagem"):
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[database]
        self.fs = AsyncIOMotorGridFSBucket(self.db)
        self.users = self.db["users"]
        self.chat_sessions = self.db["chat_sessions"]
        self.analyses = self.db["analyses"]
        logger.info("database_service_initialized")
    
    async def initialize(self):
        """Create indexes for all collections."""
        # Users indexes
        await self.users.create_index("email", unique=True)
        
        # Chat sessions indexes
        await self.chat_sessions.create_index("user_id")
        await self.chat_sessions.create_index("updated_at")
        await self.chat_sessions.create_index([("user_id", 1), ("updated_at", -1)])
        
        # Analyses indexes
        await self.analyses.create_index("user_id")
        await self.analyses.create_index("created_at")
        
        logger.info("database_indexes_created")
    
    # ==================== User Operations ====================
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        user_data["_id"] = str(uuid.uuid4())
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        
        await self.users.insert_one(user_data)
        logger.info("user_created", user_id=user_data["_id"])
        return user_data
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find a user by email."""
        user = await self.users.find_one({"email": email.lower()})
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find a user by ID."""
        user = await self.users.find_one({"_id": user_id})
        return user
    
    # ==================== Chat Session Operations ====================
    
    async def create_chat_session(self, user_id: str, title: str = "New Chat") -> Dict[str, Any]:
        """Create a new chat session."""
        session = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": title,
            "messages": [],
            "company_name": None,
            "industry": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        await self.chat_sessions.insert_one(session)
        logger.info("chat_session_created", session_id=session["_id"], user_id=user_id)
        return session
    
    async def get_chat_session(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat session by ID, ensuring it belongs to the user."""
        session = await self.chat_sessions.find_one({
            "_id": session_id,
            "user_id": user_id
        })
        return session
    
    async def add_message_to_session(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str
    ) -> bool:
        """Add a message to a chat session."""
        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self.chat_sessions.update_one(
            {"_id": session_id, "user_id": user_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
    
    async def update_session_title(self, session_id: str, user_id: str, title: str) -> bool:
        """Update a chat session's title."""
        result = await self.chat_sessions.update_one(
            {"_id": session_id, "user_id": user_id},
            {"$set": {"title": title, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    async def update_session_metadata(
        self,
        session_id: str,
        user_id: str,
        company_name: Optional[str] = None,
        industry: Optional[str] = None
    ) -> bool:
        """Update session metadata (company name, industry)."""
        update = {"$set": {"updated_at": datetime.utcnow()}}
        if company_name is not None:
            update["$set"]["company_name"] = company_name
        if industry is not None:
            update["$set"]["industry"] = industry
        
        result = await self.chat_sessions.update_one(
            {"_id": session_id, "user_id": user_id},
            update
        )
        return result.modified_count > 0
    
    async def list_user_sessions(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """List all chat sessions for a user, most recent first."""
        cursor = self.chat_sessions.find(
            {"user_id": user_id},
            {
                "_id": 1,
                "title": 1,
                "company_name": 1,
                "created_at": 1,
                "updated_at": 1,
                # Include first message preview
                "messages": {"$slice": 1}
            }
        ).sort("updated_at", -1).skip(skip).limit(limit)
        
        sessions = await cursor.to_list(length=limit)
        
        # Format for frontend
        result = []
        for s in sessions:
            first_msg = s.get("messages", [{}])
            preview = ""
            if first_msg:
                preview = first_msg[0].get("content", "")[:80] if first_msg else ""
            
            result.append({
                "id": s["_id"],
                "title": s.get("title", "New Chat"),
                "company_name": s.get("company_name"),
                "preview": preview,
                "created_at": s.get("created_at", datetime.utcnow()).isoformat(),
                "updated_at": s.get("updated_at", datetime.utcnow()).isoformat(),
            })
        
        return result
    
    async def delete_chat_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session."""
        result = await self.chat_sessions.delete_one({
            "_id": session_id,
            "user_id": user_id
        })
        if result.deleted_count > 0:
            logger.info("chat_session_deleted", session_id=session_id)
            return True
        return False
    
    # ==================== Analysis Operations ====================
    
    async def save_analysis(self, user_id: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save an analysis result."""
        analysis_data["user_id"] = user_id
        analysis_data["created_at"] = datetime.utcnow()
        
        if "_id" not in analysis_data:
            analysis_data["_id"] = str(uuid.uuid4())
        
        await self.analyses.insert_one(analysis_data)
        logger.info("analysis_saved", analysis_id=analysis_data["_id"], user_id=user_id)
        return analysis_data
    
    async def list_user_analyses(
        self,
        user_id: str,
        limit: int = 20,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """List analyses for a user."""
        cursor = self.analyses.find(
            {"user_id": user_id},
            {
                "_id": 1,
                "company_name": 1,
                "status": 1,
                "summary": 1,
                "execution_time": 1,
                "created_at": 1,
                "output_urls": 1
            }
        ).sort("created_at", -1).skip(skip).limit(limit)
        
        results = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            results.append(doc)
            
        return results
    
    async def close(self):
        """Close MongoDB connection."""
        self.client.close()
        logger.info("database_service_closed")

    # ==================== Comparison & File Storage ====================

    async def save_comparison(self, comparison_data: Dict[str, Any]):
        """Save comparison data."""
        # Use comparison_id as the primary key for queries
        await self.db.comparisons.update_one(
            {"comparison_id": comparison_data["comparison_id"]},
            {"$set": comparison_data},
            upsert=True
        )

    async def get_comparison(self, comparison_id: str) -> Optional[Dict[str, Any]]:
        """Get comparison data."""
        return await self.db.comparisons.find_one({"comparison_id": comparison_id})

    async def upload_file(self, filename: str, data: bytes, content_type: str, metadata: Dict[str, Any] = None) -> str:
        """Upload a file to GridFS."""
        file_id = await self.fs.upload_from_stream(
            filename,
            data,
            metadata={"contentType": content_type, **(metadata or {})}
        )
        return str(file_id)

    async def get_file(self, file_id: str) -> Optional[bytes]:
        """Download a file from GridFS."""
        from bson import ObjectId
        try:
            grid_out = await self.fs.open_download_stream(ObjectId(file_id))
            return await grid_out.read()
        except Exception as e:
            logger.error(f"gridfs_download_failed: {e}")
            return None
