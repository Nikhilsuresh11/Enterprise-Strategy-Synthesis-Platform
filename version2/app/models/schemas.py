"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AnalysisRequest(BaseModel):
    """Request model for company analysis."""
    
    company_name: str = Field(..., description="Name of the company to analyze")
    industry: Optional[str] = Field(None, description="Industry sector (optional)")
    question: str = Field(..., description="Strategic question or analysis focus")
    include_mna: bool = Field(False, description="Include M&A/partnership analysis")
    output_format: List[str] = Field(
        default=["pdf", "json"],
        description="Desired output formats: pdf, ppt, json"
    )
    # Optional: answers to clarifying questions
    question_answers: Optional[Dict[str, str]] = Field(
        None,
        description="Answers to clarifying questions (if provided)"
    )


class QuestionRequest(BaseModel):
    """Request model for generating clarifying questions."""
    
    company_name: str = Field(..., description="Name of the company")
    industry: Optional[str] = Field(None, description="Industry sector")
    question: str = Field(..., description="User's strategic question")


class QuestionResponse(BaseModel):
    """Response model for clarifying questions."""
    
    questions: List[Dict[str, Any]] = Field(
        ...,
        description="List of clarifying questions with options"
    )


class AnalysisResponse(BaseModel):
    """Response model for completed analysis."""
    
    analysis_id: str
    company_name: str
    status: str  # "completed", "failed", "in_progress"
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # Results
    summary: Optional[str] = None
    output_urls: Optional[List[str]] = None  # List of file paths
    
    # Metadata
    execution_time: Optional[float] = None
    token_usage: Optional[Dict[str, int]] = None
    errors: Optional[List[str]] = None


class ProgressUpdate(BaseModel):
    """WebSocket progress update model."""
    
    analysis_id: str
    stage: str  # "profiling", "research", "analysis", "synthesis", "validation"
    progress: int  # 0-100
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
