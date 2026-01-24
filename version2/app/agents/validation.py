"""Validation Agent - Quality assurance and consistency checking."""

from typing import Dict, Any
from app.agents.base import BaseAgent
from app.models.state import AgentState
from app.services.llm_service import LLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ValidationAgent(BaseAgent):
    """
    Agent 6: Validation & Quality Assurance
    
    Responsibilities:
    - Validate strategy for logical consistency
    - Check for unsupported claims
    - Identify gaps in analysis
    - Calculate confidence scores
    - Provide improvement suggestions
    
    Data Sources:
    - All previous agent outputs
    
    Model: Llama 3.3 70B (critical reasoning required)
    
    Note: Can trigger feedback loop to re-run Strategy Agent if critical gaps found
    """
    
    def __init__(self, llm: LLMService):
        super().__init__("validation")
        self.llm = llm
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute validation and quality checks.
        
        Args:
            state: Current agent state with strategy synthesis
        
        Returns:
            State with 'validation_results' populated
        """
        # Validate input
        if not self._validate_state(state, ["strategy_synthesis"]):
            return state
        
        company_name = state["company_profile"]["name"]
        
        logger.info("validating_analysis", company=company_name)
        
        # Perform validation
        validation = await self._validate_analysis(
            company_name=company_name,
            strategy_synthesis=state.get("strategy_synthesis", {}),
            market_analysis=state.get("market_analysis", {}),
            financial_model=state.get("financial_model", {}),
            risk_assessment=state.get("risk_assessment", {}),
            state=state
        )
        
        # Update state
        state["validation_results"] = validation
        
        logger.info(
            "validation_completed",
            company=company_name,
            confidence_score=validation.get("confidence_score", 0),
            critical_gaps=len(validation.get("critical_gaps", []))
        )
        
        return state
    
    async def _validate_analysis(
        self,
        company_name: str,
        strategy_synthesis: Dict[str, Any],
        market_analysis: Dict[str, Any],
        financial_model: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        state: AgentState = None
    ) -> Dict[str, Any]:
        """Validate strategic analysis for quality and consistency."""
        
        # Check for dynamic prompt from Intent Analyzer
        dynamic_prompts = state.get("dynamic_prompts", {}) if state else {}
        custom_prompt = dynamic_prompts.get("validation")
        
        if custom_prompt:
            # Use MBB-grade Quality Assurance prompt
            logger.info("using_dynamic_prompt", agent="validation")
            
            prompt = f"""{custom_prompt}

Analysis to Validate:
- Strategy: {self._format_dict(strategy_synthesis, 300)}
- Market: {self._format_dict(market_analysis, 200)}
- Financials: {self._format_dict(financial_model, 200)}
- Risks: {self._format_dict(risk_assessment, 200)}

Return ONLY a JSON object:
{{
    "quality_checks": [
        {{
            "check": "Framework Alignment",
            "status": "pass/fail/warning",
            "note": "One sentence assessment of strategic framework usage"
        }},
        {{
            "check": "Data Consistency",
            "status": "pass/fail/warning",
            "note": "One sentence assessment of data coherence"
        }},
        {{
            "check": "Actionability",
            "status": "pass/fail/warning",
            "note": "One sentence assessment of recommendation specificity"
        }},
        {{
            "check": "MECE Compliance",
            "status": "pass/fail/warning",
            "note": "One sentence assessment of mutually exclusive, collectively exhaustive structure"
        }}
    ],
    "confidence_score": 0.85,
    "overall_assessment": "One sentence overall quality assessment",
    "critical_gaps": []
}}

Focus on: framework alignment, data consistency, actionability, MECE compliance. Set critical_gaps only if fundamental flaws require re-analysis.
"""
        else:
            # Fallback to default prompt
            logger.info("using_default_prompt", agent="validation")
            
            prompt = f"""Validate the strategic analysis for {company_name} and provide 3-4 QUALITY CHECKS.

Analysis to Validate:
- Strategy: {self._format_dict(strategy_synthesis, 300)}
- Market: {self._format_dict(market_analysis, 200)}
- Financials: {self._format_dict(financial_model, 200)}
- Risks: {self._format_dict(risk_assessment, 200)}

Return ONLY a JSON object:
{{
    "quality_checks": [
        {{
            "check": "Completeness",
            "status": "pass/fail/warning",
            "note": "One sentence assessment"
        }},
        {{
            "check": "Consistency",
            "status": "pass/fail/warning",
            "note": "One sentence assessment"
        }},
        {{
            "check": "Actionability",
            "status": "pass/fail/warning",
            "note": "One sentence assessment"
        }}
    ],
    "confidence_score": 0.85,
    "overall_assessment": "One sentence overall quality assessment",
    "critical_gaps": []
}}

Focus on: completeness, consistency, actionability. Each note should be ONE concise sentence.
Set critical_gaps only if fundamental flaws require re-analysis.
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            task_type="reasoning",  # Use Llama 3.3 70B
            temperature=0.2,  # Low temperature for critical analysis
            max_tokens=700  # Reduced
        )
        
        # Parse JSON
        try:
            import json
            import re
            
            try:
                validation = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    validation = json.loads(json_match.group(0))
                else:
                    raise
            
            # Ensure confidence_score is float
            if "confidence_score" in validation:
                validation["confidence_score"] = float(validation["confidence_score"])
            else:
                validation["confidence_score"] = 0.7  # Default
            
            # Ensure critical_gaps is list
            if "critical_gaps" not in validation:
                validation["critical_gaps"] = []
            
            return validation
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("validation_json_parse_failed", error=str(e))
            return {
                "quality_checks": [
                    {"check": "Validation", "status": "warning", "note": "Parsing error occurred"}
                ],
                "confidence_score": 0.6,
                "critical_gaps": [],
                "overall_assessment": "Validation completed with parsing errors"
            }
    
    def _format_dict(self, data: Dict[str, Any], max_length: int = 500) -> str:
        """Format dictionary for prompt."""
        import json
        formatted = json.dumps(data, indent=2)
        if len(formatted) > max_length:
            formatted = formatted[:max_length] + "..."
        return formatted
