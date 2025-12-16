"""LangGraph state definition for agent orchestration."""

from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict):
    """
    State object passed between agents in the LangGraph workflow.
    
    This TypedDict defines the complete state structure that flows through
    the multi-agent system, accumulating data from each agent's execution.
    """
    
    # Input
    request: Dict[str, Any]  # AnalysisRequest as dict
    
    # Research Phase
    research_data: Dict[str, Any]  # Raw research data from web/APIs
    rag_context: List[Dict[str, Any]]  # Retrieved context from Pinecone
    
    # Analysis Phase
    market_analysis: Dict[str, Any]  # Market trends and insights
    financial_model: Dict[str, Any]  # Financial projections and models
    regulatory_findings: Dict[str, Any]  # Regulatory compliance analysis
    competitor_analysis: List[Dict[str, Any]]  # Competitor landscape
    
    # Synthesis Phase
    synthesis: Dict[str, Any]  # Synthesized recommendations
    slides: List[Dict[str, Any]]  # Generated presentation slides
    
    # Output
    output_paths: Dict[str, str]  # Paths to generated files
    
    # Metadata
    errors: List[str]  # Accumulated errors during execution
    metadata: Dict[str, Any]  # Additional metadata (timing, agent logs, etc.)
