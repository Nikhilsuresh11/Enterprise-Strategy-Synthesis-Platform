"""Risk Assessment Agent - Identifies and analyzes multi-dimensional risks."""

from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.models.state import AgentState
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RiskAssessmentAgent(BaseAgent):
    """
    Agent 4: Risk Assessment
    
    Responsibilities:
    - Identify regulatory and compliance risks
    - Assess operational risks (supply chain, technology, talent)
    - Evaluate financial risks (liquidity, debt, market)
    - Analyze geopolitical and ESG risks
    - Provide mitigation recommendations
    
    Data Sources:
    - RAG (regulatory frameworks, risk databases)
    - Company profile and financial data
    - LLM reasoning
    
    Model: Llama 3.3 70B (multi-dimensional reasoning)
    
    Note: Runs in parallel with Market Research and Financial Analysis
    """
    
    def __init__(
        self,
        llm: LLMService,
        rag: RAGService
    ):
        super().__init__("risk_assessment")
        self.llm = llm
        self.rag = rag
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute risk assessment.
        
        Args:
            state: Current agent state with company and market data
        
        Returns:
            State with 'risk_assessment' populated
        """
        # Validate input
        if not self._validate_state(state, ["company_profile"]):
            return state
        
        company_name = state["company_profile"]["name"]
        industry = state["company_profile"].get("industry", "Unknown")
        
        logger.info("assessing_risks", company=company_name, industry=industry)
        
        # Query RAG for regulatory and risk information
        rag_context = await self.rag.query(
            query_text=f"risks regulations compliance {industry}",
            top_k=3,
            filter={"type": "regulatory"} if industry != "Unknown" else None
        )
        
        # Build risk assessment
        risk_data = await self._assess_risks(
            company_name=company_name,
            industry=industry,
            company_profile=state["company_profile"],
            market_analysis=state.get("market_analysis", {}),
            financial_model=state.get("financial_model", {}),
            rag_context=rag_context,
            state=state
        )
        
        # Update state
        state["risk_assessment"] = risk_data
        
        logger.info("risk_assessment_completed", company=company_name)
        
        return state
    
    async def _assess_risks(
        self,
        company_name: str,
        industry: str,
        company_profile: Dict[str, Any],
        market_analysis: Dict[str, Any],
        financial_model: Dict[str, Any],
        rag_context: List[Dict[str, Any]],
        state: AgentState = None
    ) -> Dict[str, Any]:
        """Conduct comprehensive risk assessment."""
        
        # Build context
        context_text = "\n".join([
            f"- {doc['text'][:200]}" for doc in rag_context
        ]) if rag_context else "No regulatory context available"
        
        # Check for dynamic prompt from Intent Analyzer
        dynamic_prompts = state.get("dynamic_prompts", {}) if state else {}
        custom_prompt = dynamic_prompts.get("risk_assessment")
        
        if custom_prompt:
            # Use MBB-grade Risk Matrix prompt
            logger.info("using_dynamic_prompt", agent="risk_assessment")
            
            prompt = f"""{custom_prompt}

Company Context:
- Business: {company_profile.get('key_facts', ['Unknown'])[0] if company_profile.get('key_facts') else 'Unknown'}
- Market: {market_analysis.get('key_insights', ['Unknown'])[0] if market_analysis.get('key_insights') else 'Unknown'}
- Financials: {financial_model.get('key_highlights', ['Unknown'])[0] if financial_model.get('key_highlights') else 'Unknown'}

Regulatory Context:
{context_text}

Return ONLY a JSON object:
{{
    "top_risks": [
        {{
            "risk": "Risk 1 name",
            "severity": "high/medium/low",
            "likelihood": "high/medium/low",
            "description": "One sentence describing the risk and potential impact",
            "mitigation": "One sentence mitigation strategy"
        }},
        {{
            "risk": "Risk 2 name",
            "severity": "high/medium/low",
            "likelihood": "high/medium/low",
            "description": "One sentence describing the risk and potential impact",
            "mitigation": "One sentence mitigation strategy"
        }},
        {{
            "risk": "Risk 3 name",
            "severity": "high/medium/low",
            "likelihood": "high/medium/low",
            "description": "One sentence describing the risk and potential impact",
            "mitigation": "One sentence mitigation strategy"
        }},
        {{
            "risk": "Risk 4 name",
            "severity": "high/medium/low",
            "likelihood": "high/medium/low",
            "description": "One sentence describing the risk and potential impact",
            "mitigation": "One sentence mitigation strategy"
        }}
    ]
}}

Use Risk Matrix framework (Severity × Likelihood). Focus on CRITICAL risks. Each description should be ONE concise sentence.
"""
        else:
            # Fallback to default prompt
            logger.info("using_default_prompt", agent="risk_assessment")
            
            prompt = f"""Identify the TOP 4-5 RISKS for {company_name} in {industry}.

Company Context:
- Business: {company_profile.get('key_facts', ['Unknown'])[0] if company_profile.get('key_facts') else 'Unknown'}
- Market: {market_analysis.get('key_insights', ['Unknown'])[0] if market_analysis.get('key_insights') else 'Unknown'}
- Financials: {financial_model.get('key_highlights', ['Unknown'])[0] if financial_model.get('key_highlights') else 'Unknown'}

Regulatory Context:
{context_text}

Return ONLY a JSON object:
{{
    "top_risks": [
        {{
            "risk": "Risk 1 name",
            "severity": "high/medium/low",
            "description": "One sentence describing the risk and potential impact"
        }},
        {{
            "risk": "Risk 2 name",
            "severity": "high/medium/low",
            "description": "One sentence describing the risk and potential impact"
        }},
        {{
            "risk": "Risk 3 name",
            "severity": "high/medium/low",
            "description": "One sentence describing the risk and potential impact"
        }},
        {{
            "risk": "Risk 4 name",
            "severity": "high/medium/low",
            "description": "One sentence describing the risk and potential impact"
        }}
    ]
}}

Focus on the MOST CRITICAL risks. Each description should be ONE concise sentence.
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            task_type="reasoning",  # Use Llama 3.3 70B
            temperature=0.3,
            max_tokens=700  # Reduced
        )
        
        # Parse JSON
        try:
            import json
            import re
            
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                else:
                    raise
            
            return data
            
        except (json.JSONDecodeError, Exception):
            logger.warning("risk_assessment_json_parse_failed")
            return {
                "top_risks": [
                    {
                        "risk": "Risk assessment unavailable",
                        "severity": "unknown",
                        "description": "Unable to analyze risks"
                    }
                ]
            }
