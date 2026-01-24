"""Strategy Synthesis Agent - Generates strategic recommendations."""

from typing import Dict, Any
from app.agents.base import BaseAgent
from app.models.state import AgentState
from app.services.llm_service import LLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StrategySynthesisAgent(BaseAgent):
    """
    Agent 5: Strategy Synthesis
    
    Responsibilities:
    - Synthesize all previous analysis into strategic insights
    - Generate SWOT analysis
    - Develop strategic options and recommendations
    - Create implementation roadmap
    - Define success metrics
    
    Data Sources:
    - All previous agent outputs
    - User's strategic question
    
    Model: Llama 3.3 70B (high-quality synthesis required)
    
    Note: Runs after all parallel agents complete
    """
    
    def __init__(self, llm: LLMService):
        super().__init__("strategy_synthesis")
        self.llm = llm
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute strategy synthesis.
        
        Args:
            state: Current agent state with all analysis complete
        
        Returns:
            State with 'strategy_synthesis' populated
        """
        # Validate input
        required = ["company_profile", "market_analysis", "financial_model", "risk_assessment"]
        if not self._validate_state(state, required):
            logger.warning("missing_required_data_for_synthesis")
            # Continue anyway with available data
        
        company_name = state["company_profile"]["name"]
        question = state["request"].get("question", "General strategic analysis")
        
        logger.info("synthesizing_strategy", company=company_name, question=question[:50])
        
        # Synthesize strategy
        strategy = await self._synthesize_strategy(
            company_name=company_name,
            question=question,
            company_profile=state.get("company_profile", {}),
            market_analysis=state.get("market_analysis", {}),
            competitor_analysis=state.get("competitor_analysis", []),
            financial_model=state.get("financial_model", {}),
            risk_assessment=state.get("risk_assessment", {}),
            state=state
        )
        
        # Update state
        state["strategy_synthesis"] = strategy
        
        logger.info("strategy_synthesis_completed", company=company_name)
        
        return state
    
    async def _synthesize_strategy(
        self,
        company_name: str,
        question: str,
        company_profile: Dict[str, Any],
        market_analysis: Dict[str, Any],
        competitor_analysis: list,
        financial_model: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        state: AgentState = None
    ) -> Dict[str, Any]:
        """Synthesize comprehensive strategic recommendations."""
        
        # Check for dynamic prompt from Intent Analyzer
        dynamic_prompts = state.get("dynamic_prompts", {}) if state else {}
        custom_prompt = dynamic_prompts.get("strategy_synthesis")
        
        if custom_prompt:
            # Use MBB-grade Ansoff Matrix + SWOT prompt
            logger.info("using_dynamic_prompt", agent="strategy_synthesis")
            
            prompt = f"""{custom_prompt}

Strategic Question: {question}

Analysis Summary:
- Company: {self._format_dict(company_profile, 200)}
- Market: {self._format_dict(market_analysis, 200)}
- Financials: {self._format_dict(financial_model, 200)}
- Risks: {self._format_dict(risk_assessment, 200)}

Return ONLY a JSON object:
{{
    "executive_summary": "2-3 sentence strategic summary answering the question using Ansoff Matrix perspective",
    "key_recommendations": [
        "Recommendation 1: Specific Ansoff quadrant strategy (Market Penetration/Development/Product Development/Diversification)",
        "Recommendation 2: Specific, actionable strategic move",
        "Recommendation 3: Specific, actionable strategic move",
        "Recommendation 4: Specific, actionable strategic move"
    ],
    "swot_summary": {{
        "top_strength": "One key strength",
        "top_weakness": "One key weakness",
        "top_opportunity": "One key opportunity",
        "top_threat": "One key threat"
    }}
}}

Focus on Ansoff Matrix (Market Penetration, Market Development, Product Development, Diversification) and SWOT. Be specific.
"""
        else:
            # Fallback to default prompt
            logger.info("using_default_prompt", agent="strategy_synthesis")
            
            prompt = f"""Synthesize strategic recommendations for {company_name} based on all analysis.

Strategic Question: {question}

Analysis Summary:
- Company: {self._format_dict(company_profile, 200)}
- Market: {self._format_dict(market_analysis, 200)}
- Financials: {self._format_dict(financial_model, 200)}
- Risks: {self._format_dict(risk_assessment, 200)}

Return ONLY a JSON object:
{{
    "executive_summary": "2-3 sentence strategic summary answering the question",
    "key_recommendations": [
        "Recommendation 1: Specific, actionable strategic move",
        "Recommendation 2: Specific, actionable strategic move",
        "Recommendation 3: Specific, actionable strategic move",
        "Recommendation 4: Specific, actionable strategic move"
    ],
    "swot_summary": {{
        "top_strength": "One key strength",
        "top_weakness": "One key weakness",
        "top_opportunity": "One key opportunity",
        "top_threat": "One key threat"
    }}
}}

Each recommendation should be ONE concise, actionable sentence. Focus on high-impact strategic moves.
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            task_type="synthesis",  # Use Llama 3.3 70B
            temperature=0.4,  # Slightly higher for creative strategy
            max_tokens=3000
        )
        
        # Parse JSON with robust error handling
        try:
            import json
            import re
            
            # Try direct JSON parse first
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                
                # Try to find JSON object in response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                
                # If all parsing fails, extract executive summary from text
                logger.warning("strategy_synthesis_json_parse_failed_extracting_summary")
                
                # Try to extract executive summary from text
                summary_match = re.search(r'(?:executive[_ ]summary|summary)[\s:]*["\']?([^"\']+)["\']?', response, re.IGNORECASE)
                executive_summary = summary_match.group(1).strip() if summary_match else response[:200]
                
                return {
                    "executive_summary": executive_summary,
                    "swot_analysis": {},
                    "strategic_options": [],
                    "recommended_strategy": {},
                    "raw_response": response[:500]  # Store partial response for debugging
                }
                
        except Exception as e:
            logger.error("strategy_synthesis_parsing_error", error=str(e))
            return {
                "executive_summary": "Error parsing strategic analysis",
                "swot_analysis": {},
                "strategic_options": [],
                "recommended_strategy": {},
                "error": str(e)
            }
    
    def _format_dict(self, data: Dict[str, Any], max_length: int = 500) -> str:
        """Format dictionary for prompt."""
        import json
        formatted = json.dumps(data, indent=2)
        if len(formatted) > max_length:
            formatted = formatted[:max_length] + "..."
        return formatted
    
    def _format_list(self, data: list, max_items: int = 5) -> str:
        """Format list for prompt."""
        import json
        items = data[:max_items]
        return json.dumps(items, indent=2)
