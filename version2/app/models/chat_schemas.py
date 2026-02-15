"""Chat-related schemas for conversational interface."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    """Single chat message."""
    
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Request to send a chat message."""
    
    session_id: Optional[str] = Field(None, description="Chat session ID")
    message: str = Field(..., description="User message")
    company_name: Optional[str] = Field(None, description="Company being discussed")
    industry: Optional[str] = Field(None, description="Industry")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    
    session_id: str = Field(..., description="Chat session ID")
    message: str = Field(..., description="AI response")
    action: str = Field(
        ...,
        description="Next action: 'continue_chat' | 'ready_for_analysis' | 'analyzing'"
    )
    ready_to_analyze: bool = Field(
        default=False,
        description="Whether enough context has been gathered"
    )
    companies: List[str] = Field(
        default=[],
        description="Detected company names"
    )
    analysis_type: str = Field(
        default="single",
        description="'single' | 'comparison'"
    )


class StartAnalysisRequest(BaseModel):
    """Request to start analysis from chat."""
    
    session_id: str = Field(..., description="Chat session ID")
    chat_history: List[ChatMessage] = Field(..., description="Full chat history")
    company_name: str = Field(..., description="Company name")
    industry: Optional[str] = Field(None, description="Industry")
    output_format: List[str] = Field(
        default=["json", "ppt"],
        description="Output formats"
    )
