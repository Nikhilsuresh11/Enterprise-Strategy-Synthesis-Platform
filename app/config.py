"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    groq_api_key: str = Field(..., description="Groq API key for LLM access")
    newsapi_key: str = Field(default="", description="NewsAPI key (optional, free tier available)")
    
    # MongoDB Configuration
    mongodb_uri: str = Field(
        ...,
        description="MongoDB connection URI"
    )
    mongodb_db_name: str = Field(
        default="stratagem_ai",
        description="MongoDB database name"
    )
    
    # Pinecone Configuration
    pinecone_api_key: str = Field(..., description="Pinecone API key for vector DB")
    pinecone_environment: str = Field(..., description="Pinecone environment")
    pinecone_index_name: str = Field(
        default="stratagem-rag",
        description="Pinecone index name"
    )
    
    # Embedding Configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model to use (Sentence Transformers)"
    )
    embedding_dimension: int = Field(
        default=384,
        description="Embedding dimension (384 for all-MiniLM-L6-v2)"
    )
    
    # RAG Configuration
    rag_top_k: int = Field(
        default=10,
        description="Number of documents to retrieve"
    )
    rag_similarity_threshold: float = Field(
        default=0.7,
        description="Minimum similarity score for retrieval"
    )
    chunk_size: int = Field(
        default=1000,
        description="Document chunk size in characters"
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap between chunks"
    )
    
    # Application Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    max_concurrent_agents: int = Field(
        default=4,
        description="Maximum number of concurrent agent executions"
    )
    
    # Optional Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Cached application settings
    """
    return Settings()
