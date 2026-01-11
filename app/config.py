"""Configuration management using Pydantic Settings."""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    groq_api_key: str = Field(..., description="Groq API key for LLM access")
    openrouter_api_key: str = Field(default="", description="OpenRouter API key (fallback provider)")
    newsapi_key: str = Field(default="", description="NewsAPI key (optional, free tier available)")
    
    # LLM Configuration
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Default Groq model for complex reasoning"
    )
    groq_fast_model: str = Field(
        default="llama-3-8b-8192",
        description="Fast Groq model for lightweight tasks"
    )
    openrouter_model: str = Field(
        default="google/gemini-2.0-flash-exp:free",
        description="OpenRouter model to use as fallback"
    )
    openrouter_site_url: str = Field(
        default="",
        description="Site URL for OpenRouter rankings (optional)"
    )
    openrouter_site_name: str = Field(
        default="Enterprise Strategy Platform",
        description="Site name for OpenRouter rankings (optional)"
    )
    llm_max_retries: int = Field(
        default=5,
        description="Maximum number of retries for LLM requests"
    )
    llm_retry_delay: float = Field(
        default=3.0,
        description="Initial retry delay in seconds (exponential backoff)"
    )
    llm_rate_limit_delay: float = Field(
        default=2.0,
        description="Delay between LLM requests to prevent rate limiting"
    )
    
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
        default="sentence-transformers/all-mpnet-base-v2",
        description="Embedding model (upgraded for better quality)"
    )
    embedding_dimension: int = Field(
        default=768,
        description="Embedding dimension (768 for all-mpnet-base-v2)"
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
        default=8,
        description="Maximum number of concurrent agent executions (increased for speed)"
    )
    
    # API Configuration - Render Compatible
    api_host: str = Field(
        default="0.0.0.0", 
        description="API host (must be 0.0.0.0 for Render)"
    )
    port: int = Field(
        default=8080,
        description="API port (Pydantic reads from PORT env var automatically)"
    )
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )

    # Feature Flags
    enable_rag: bool = Field(
        default=False,
        description="Enable RAG service (requires Pinecone & Sentence Transformers)"
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