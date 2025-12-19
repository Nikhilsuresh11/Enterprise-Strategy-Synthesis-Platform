"""LangGraph orchestrator for coordinating all agents."""

import asyncio
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from app.models.state import AgentState
from app.agents.researcher import ResearchAgent
from app.agents.analyst import AnalystAgent
from app.agents.regulatory import RegulatoryAgent
from app.agents.synthesizer import SynthesizerAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StratagemOrchestrator:
    """
    LangGraph orchestrator coordinating all agents:
    
    Workflow:
    START → Research → (Analyst || Regulatory) → Synthesizer → END
    
    Analyst and Regulatory run in PARALLEL for speed.
    """
    
    def __init__(
        self,
        research_agent: ResearchAgent,
        analyst_agent: AnalystAgent,
        regulatory_agent: RegulatoryAgent,
        synthesizer_agent: SynthesizerAgent
    ):
        """
        Initialize orchestrator with all agents.
        
        Args:
            research_agent: Research agent instance
            analyst_agent: Analyst agent instance
            regulatory_agent: Regulatory agent instance
            synthesizer_agent: Synthesizer agent instance
        """
        self.research = research_agent
        self.analyst = analyst_agent
        self.regulatory = regulatory_agent
        self.synthesizer = synthesizer_agent
        
        self.workflow = self._build_workflow()
        
        logger.info("orchestrator_initialized")
    
    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow with parallel execution.
        
        Returns:
            Compiled workflow graph
        """
        # Use AgentState type for proper state management
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("research", self.research.execute)
        workflow.add_node("analyst", self.analyst.execute)
        workflow.add_node("regulatory", self.regulatory.execute)
        workflow.add_node("synthesizer", self.synthesizer.execute)
        
        # Define workflow edges
        # Start with research
        workflow.set_entry_point("research")
        
        # After research, go to analyst
        workflow.add_edge("research", "analyst")
        
        # After analyst, go to regulatory
        workflow.add_edge("analyst", "regulatory")
        
        # After regulatory, go to synthesizer
        workflow.add_edge("regulatory", "synthesizer")
        
        # End after synthesis
        workflow.add_edge("synthesizer", END)
        
        return workflow.compile()
    
    async def execute(self, initial_state: AgentState) -> AgentState:
        """
        Execute complete workflow.
        
        Note: Analyst and Regulatory run sequentially in this version.
        For true parallel execution, we'd need to restructure the state handling.
        
        Args:
            initial_state: Initial state with request
            
        Returns:
            Final state with all analysis complete
        """
        try:
            logger.info(
                "orchestrator_starting",
                company=initial_state["request"]["company_name"]
            )
            
            # Execute workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            logger.info(
                "orchestrator_complete",
                total_time=sum([
                    final_state["metadata"].get("research_time", 0),
                    final_state["metadata"].get("analyst_time", 0),
                    final_state["metadata"].get("regulatory_time", 0),
                    final_state["metadata"].get("synthesis_time", 0)
                ]),
                errors=len(final_state.get("errors", []))
            )
            
            return final_state
            
        except Exception as e:
            logger.error("orchestrator_failed", error=str(e), exc_info=True)
            # Ensure errors list exists
            if "errors" not in initial_state:
                initial_state["errors"] = []
            initial_state["errors"].append(f"Orchestrator failed: {str(e)}")
            return initial_state


async def create_orchestrator(
    research_agent: ResearchAgent,
    analyst_agent: AnalystAgent,
    regulatory_agent: RegulatoryAgent,
    synthesizer_agent: SynthesizerAgent
) -> StratagemOrchestrator:
    """
    Factory function to create orchestrator.
    
    Args:
        research_agent: Research agent
        analyst_agent: Analyst agent
        regulatory_agent: Regulatory agent
        synthesizer_agent: Synthesizer agent
        
    Returns:
        Configured orchestrator
    """
    return StratagemOrchestrator(
        research_agent,
        analyst_agent,
        regulatory_agent,
        synthesizer_agent
    )
