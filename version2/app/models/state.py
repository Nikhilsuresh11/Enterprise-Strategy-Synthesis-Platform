"""LangGraph state definition for agent orchestration."""

from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """
    State object passed between agents in the LangGraph workflow.
    
    This TypedDict defines the complete state structure that flows through
    the multi-agent system, accumulating data from each agent's execution.
    """
    
    # Input
    request: Dict[str, Any]  # User request with company_name, question, etc.
    
    # Agent Outputs
    company_profile: Dict[str, Any]  # Basic company information
    market_analysis: Dict[str, Any]  # Market trends and landscape
    competitor_analysis: List[Dict[str, Any]]  # Competitor information
    financial_model: Dict[str, Any]  # Financial analysis and projections
    risk_assessment: Dict[str, Any]  # Multi-dimensional risk analysis
    strategy_synthesis: Dict[str, Any]  # Strategic recommendations
    validation_results: Dict[str, Any]  # Quality validation results
    
    # Output
    final_report: Dict[str, Any]  # Generated report content
    output_paths: Dict[str, str]  # Paths to PDF/PPT/JSON files
    
    # Metadata
    errors: List[str]  # Accumulated errors during execution
    metadata: Dict[str, Any]  # Timing, agent logs, token usage, etc.
