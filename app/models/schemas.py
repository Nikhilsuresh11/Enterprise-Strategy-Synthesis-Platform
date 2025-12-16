"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class AnalysisType(str, Enum):
    """Types of strategic analysis."""
    
    EXPANSION = "expansion"
    ACQUISITION = "acquisition"
    INVESTMENT = "investment"
    MARKET_ENTRY = "market_entry"


class AnalysisRequest(BaseModel):
    """Request model for strategic analysis."""
    
    company_name: str = Field(
        ...,
        description="Name of the company to analyze",
        min_length=1,
        max_length=200
    )
    industry: str = Field(
        ...,
        description="Industry sector",
        min_length=1,
        max_length=100
    )
    strategic_question: str = Field(
        ...,
        description="Strategic question to answer",
        min_length=10,
        max_length=1000
    )
    analysis_type: Optional[AnalysisType] = Field(
        default=None,
        description="Type of strategic analysis"
    )
    additional_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for the analysis"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "company_name": "Tesla Inc.",
                "industry": "Automotive & Clean Energy",
                "strategic_question": "Should Tesla expand into the Indian market?",
                "analysis_type": "market_entry",
                "additional_context": {
                    "budget": "500M USD",
                    "timeline": "2-3 years"
                }
            }
        }
    }


class Citation(BaseModel):
    """Citation for research data."""
    
    source: str = Field(
        ...,
        description="Source name or publication",
        min_length=1
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to the source"
    )
    date: Optional[datetime] = Field(
        default=None,
        description="Publication or access date"
    )
    relevance_score: float = Field(
        ...,
        description="Relevance score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )


class ResearchData(BaseModel):
    """Aggregated research data from various sources."""
    
    news_articles: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="News articles related to the analysis"
    )
    financial_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Financial metrics and data"
    )
    regulatory_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Regulatory and compliance information"
    )
    competitor_data: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Competitor analysis data"
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="Citations for all research sources"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when research was conducted"
    )


class AnalysisStatus(str, Enum):
    """Status of analysis job."""
    
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisResponse(BaseModel):
    """Response model for analysis job status."""
    
    job_id: str = Field(
        ...,
        description="Unique job identifier",
        min_length=1
    )
    status: AnalysisStatus = Field(
        ...,
        description="Current status of the analysis"
    )
    progress: int = Field(
        ...,
        description="Progress percentage (0-100)",
        ge=0,
        le=100
    )
    created_at: datetime = Field(
        ...,
        description="Job creation timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Job completion timestamp"
    )
    result_urls: Optional[Dict[str, str]] = Field(
        default=None,
        description="URLs to generated outputs (deck, report, etc.)"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if job failed"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "progress": 65,
                "created_at": "2024-01-15T10:30:00Z",
                "completed_at": None,
                "result_urls": None
            }
        }
    }
