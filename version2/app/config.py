"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    groq_api_key: str
    openrouter_api_key: Optional[str] = None
    agentops_api_key: Optional[str] = None
    newsapi_key: Optional[str] = None
    
    # Database
    mongodb_uri: str
    
    # Vector Database
    pinecone_api_key: str
    pinecone_environment: str
    pinecone_index_name: str = "stratagem-knowledge"
    
    # App Settings
    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    port: int = 8000
    
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440
    
    # Model Settings
    default_model: str = "llama-3.3-70b-versatile"
    fast_model: str = "llama-3.1-8b-instant"  # Fixed: was llama-3-8b-8192
    fallback_model: str = "tngtech/deepseek-r1t2-chimera:free"  # OpenRouter free model
    
    # Rate Limits
    groq_rpm_limit: int = 14000
    groq_rpd_limit: int = 7000
    pinecone_qpm_limit: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
