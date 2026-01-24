"""LangGraph orchestrator for coordinating all agents with parallel execution and dynamic prompts."""

import asyncio
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from app.models.state import AgentState
from app.agents import (
    EnterpriseIntentAnalyzer,
    CompanyProfilingAgent,
    MarketResearchAgent,
    FinancialAnalysisAgent,
    RiskAssessmentAgent,
    StrategySynthesisAgent,
    ValidationAgent
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StratagemOrchestrator:
    """
    LangGraph orchestrator coordinating all 7 agents (including Intent Analyzer).
    
    Workflow:
    0. Intent Analyzer (if chat_history exists) - generates dynamic prompts
    1. Company Profiling (sequential)
    2. Market Research + Financial Analysis + Risk Assessment (parallel)
    3. Strategy Synthesis (sequential)
    4. Validation (sequential with feedback loop)
    
    Features:
    - Dynamic prompt generation based on user intent
    - True parallel execution using asyncio.gather()
    - Validation feedback loop
    - Error handling and state management
    """
    
    def __init__(
        self,
        profile_agent: CompanyProfilingAgent,
        market_agent: MarketResearchAgent,
        financial_agent: FinancialAnalysisAgent,
        risk_agent: RiskAssessmentAgent,
        strategy_agent: StrategySynthesisAgent,
        validation_agent: ValidationAgent,
        intent_agent: Optional[EnterpriseIntentAnalyzer] = None
    ):
        self.intent = intent_agent
        self.profile = profile_agent
        self.market = market_agent
        self.financial = financial_agent
        self.risk = risk_agent
        self.strategy = strategy_agent
        self.validation = validation_agent
        
        self.workflow = self._build_workflow()
        
        logger.info("orchestrator_initialized", has_intent_analyzer=intent_agent is not None)
    
    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow with optional Intent Analyzer and parallel execution.
        
        Returns:
            Compiled workflow graph
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        if self.intent:
            workflow.add_node("intent_analysis", self.intent.run)
        workflow.add_node("profile", self.profile.run)
        workflow.add_node("parallel_analysis", self._parallel_analysis)
        workflow.add_node("strategy", self.strategy.run)
        workflow.add_node("validation", self.validation.run)
        
        # Define flow
        if self.intent:
            workflow.set_entry_point("intent_analysis")
            workflow.add_edge("intent_analysis", "profile")
        else:
            workflow.set_entry_point("profile")
        
        workflow.add_edge("profile", "parallel_analysis")
        workflow.add_edge("parallel_analysis", "strategy")
        workflow.add_edge("strategy", "validation")
        
        # Conditional edge for feedback loop
        workflow.add_conditional_edges(
            "validation",
            self._should_refine,
            {
                "refine": "strategy",  # Re-run strategy synthesis
                "finalize": END        # Complete workflow
            }
        )
        
        return workflow.compile()
    
    async def _parallel_analysis(self, state: AgentState) -> AgentState:
        """
        Execute Market, Financial, and Risk agents in parallel.
        
        This is the key optimization - runs 3 agents concurrently
        instead of sequentially, reducing execution time by ~3x.
        
        Args:
            state: Current agent state
        
        Returns:
            State with all 3 analyses complete
        """
        logger.info("starting_parallel_analysis")
        
        try:
            # Run all 3 agents in parallel
            market_state, financial_state, risk_state = await asyncio.gather(
                self.market.run(state.copy()),
                self.financial.run(state.copy()),
                self.risk.run(state.copy())
            )
            
            # Merge results into single state
            # Each agent updates different fields, so no conflicts
            state["market_analysis"] = market_state.get("market_analysis", {})
            state["competitor_analysis"] = market_state.get("competitor_analysis", [])
            state["financial_model"] = financial_state.get("financial_model", {})
            state["risk_assessment"] = risk_state.get("risk_assessment", {})
            
            # Merge metadata
            if "metadata" not in state:
                state["metadata"] = {}
            
            for agent_state in [market_state, financial_state, risk_state]:
                if "metadata" in agent_state:
                    state["metadata"].update(agent_state["metadata"])
            
            # Merge errors
            if "errors" not in state:
                state["errors"] = []
            
            for agent_state in [market_state, financial_state, risk_state]:
                if "errors" in agent_state:
                    state["errors"].extend(agent_state["errors"])
            
            logger.info("parallel_analysis_completed")
            
        except Exception as e:
            logger.error("parallel_analysis_failed", error=str(e), exc_info=True)
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Parallel analysis failed: {str(e)}")
        
        return state
    
    def _should_refine(self, state: AgentState) -> str:
        """
        Decide if strategy needs refinement based on validation results.
        
        Triggers refinement if:
        - Critical gaps identified
        - Confidence score < 0.7
        - But only allow 1 refinement iteration to avoid infinite loops
        
        Args:
            state: Current agent state with validation results
        
        Returns:
            "refine" or "finalize"
        """
        validation = state.get("validation_results", {})
        metadata = state.get("metadata", {})
        
        # Check if we've already refined once
        refinement_count = metadata.get("refinement_count", 0)
        if refinement_count >= 1:
            logger.info("max_refinements_reached", count=refinement_count)
            return "finalize"
        
        # Check for critical gaps
        critical_gaps = validation.get("critical_gaps", [])
        if critical_gaps:
            logger.info("critical_gaps_found", gaps=critical_gaps)
            metadata["refinement_count"] = refinement_count + 1
            return "refine"
        
        # Check confidence score
        confidence = validation.get("confidence_score", 1.0)
        if confidence < 0.7:
            logger.info("low_confidence_score", score=confidence)
            metadata["refinement_count"] = refinement_count + 1
            return "refine"
        
        logger.info("validation_passed", confidence=confidence)
        return "finalize"
    
    async def execute(self, initial_state: AgentState) -> AgentState:
        """
        Execute complete workflow.
        
        Args:
            initial_state: Initial state with user request
        
        Returns:
            Final state with complete analysis
        """
        try:
            # Initialize metadata
            if "metadata" not in initial_state:
                initial_state["metadata"] = {}
            if "errors" not in initial_state:
                initial_state["errors"] = []
            
            company_name = initial_state["request"]["company_name"]
            
            logger.info(
                "orchestrator_starting",
                company=company_name
            )
            
            # Execute workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Calculate total execution time
            metadata = final_state.get("metadata", {})
            total_time = sum([
                metadata.get("company_profiling_time", 0),
                metadata.get("market_research_time", 0),
                metadata.get("financial_analysis_time", 0),
                metadata.get("risk_assessment_time", 0),
                metadata.get("strategy_synthesis_time", 0),
                metadata.get("validation_time", 0)
            ])
            
            metadata["total_execution_time"] = total_time
            final_state["metadata"] = metadata
            
            logger.info(
                "orchestrator_completed",
                company=company_name,
                total_time=total_time,
                errors=len(final_state.get("errors", [])),
                refinements=metadata.get("refinement_count", 0)
            )
            
            return final_state
            
        except Exception as e:
            logger.error("orchestrator_failed", error=str(e), exc_info=True)
            
            if "errors" not in initial_state:
                initial_state["errors"] = []
            initial_state["errors"].append(f"Orchestrator failed: {str(e)}")
            
            return initial_state


def create_orchestrator(
    profile_agent: CompanyProfilingAgent,
    market_agent: MarketResearchAgent,
    financial_agent: FinancialAnalysisAgent,
    risk_agent: RiskAssessmentAgent,
    strategy_agent: StrategySynthesisAgent,
    validation_agent: ValidationAgent,
    intent_agent: Optional[EnterpriseIntentAnalyzer] = None
) -> StratagemOrchestrator:
    """
    Factory function to create orchestrator.
    
    Args:
        All 6 agent instances + optional Intent Analyzer
    
    Returns:
        Configured orchestrator
    """
    return StratagemOrchestrator(
        profile_agent=profile_agent,
        market_agent=market_agent,
        financial_agent=financial_agent,
        risk_agent=risk_agent,
        strategy_agent=strategy_agent,
        validation_agent=validation_agent,
        intent_agent=intent_agent
    )
