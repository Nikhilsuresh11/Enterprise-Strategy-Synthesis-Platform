"""Financial Analysis Agent - Builds financial models and projections."""

from typing import Dict, Any
from app.agents.base import BaseAgent
from app.models.state import AgentState
from app.services.llm_service import LLMService
from app.services.external_apis import ExternalDataService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FinancialAnalysisAgent(BaseAgent):
    """
    Agent 3: Financial Analysis
    
    Responsibilities:
    - Analyze historical financial performance
    - Calculate key financial ratios
    - Build valuation models (DCF, P/E multiples)
    - Generate 3-year projections
    
    Data Sources:
    - Yahoo Finance (financial data)
    - LLM for analysis and projections
    
    Model: Llama 3.3 70B (complex financial reasoning)
    
    Note: Runs in parallel with Market Research and Risk Assessment
    """
    
    def __init__(
        self,
        llm: LLMService,
        external: ExternalDataService
    ):
        super().__init__("financial_analysis")
        self.llm = llm
        self.external = external
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute financial analysis.
        
        Args:
            state: Current agent state with 'company_profile'
        
        Returns:
            State with 'financial_model' populated
        """
        # Validate input
        if not self._validate_state(state, ["company_profile"]):
            return state
        
        company_name = state["company_profile"]["name"]
        ticker = state["company_profile"].get("ticker")
        
        logger.info("analyzing_financials", company=company_name, ticker=ticker)
        
        # Get financial data
        if not ticker:
            ticker = self.external.company_to_ticker(company_name)
        
        financial_data = {}
        if ticker:
            financial_data = await self.external.fetch_financial_data(ticker)
        
        # Build financial model
        if financial_data:
            model = await self._build_financial_model(
                company_name=company_name,
                financial_data=financial_data,
                state=state
            )
        else:
            logger.warning("no_financial_data_available", company=company_name)
            model = {
                "status": "unavailable",
                "reason": "No financial data found"
            }
        
        # Update state
        state["financial_model"] = model
        
        logger.info("financial_analysis_completed", company=company_name)
        
        return state
    
    async def _build_financial_model(
        self,
        company_name: str,
        financial_data: Dict[str, Any],
        state: AgentState = None
    ) -> Dict[str, Any]:
        """Build comprehensive financial model using LLM."""
        
        dynamic_prompts = state.get("dynamic_prompts", {}) if state else {}
        custom_prompt = dynamic_prompts.get("financial_analysis")
        
        # Format RAG context
        rag_context = state.get("rag_context", []) if state else []
        rag_text = "\n".join(rag_context[:3]) if rag_context else "No uploaded documents"
        
        if custom_prompt:
            # Use MBB-grade DuPont ROE Analysis prompt
            logger.info("using_dynamic_prompt", agent="financial_analysis")
            
            prompt = f"""{custom_prompt}

Financial Data:
- Market Cap: ${financial_data.get('market_cap', 0):,.0f}
- Revenue: ${financial_data.get('revenue', 0):,.0f}
- Profit Margin: {financial_data.get('profit_margin', 0):.2%}
- P/E Ratio: {financial_data.get('pe_ratio', 'N/A')}
- Current Price: ${financial_data.get('current_price', 0):.2f}
- 52-Week Range: ${financial_data.get('52_week_low', 0):.2f} - ${financial_data.get('52_week_high', 0):.2f}
- Uploaded Documents: {rag_text[:1000]}

Return ONLY a JSON object:
{{
    "key_highlights": [
        "Highlight 1: DuPont ROE component analysis",
        "Highlight 2: Profitability driver insight",
        "Highlight 3: Financial leverage assessment",
        "Highlight 4: Asset efficiency metric",
        "Highlight 5: Investment implication"
    ]
}}

Focus on DuPont ROE framework (Profit Margin × Asset Turnover × Equity Multiplier). Be specific with data.
"""
        else:
            # Fallback to default prompt
            logger.info("using_default_prompt", agent="financial_analysis")
            
            prompt = f"""Analyze {company_name}'s financials and provide 4-5 KEY HIGHLIGHTS as bullet points.

Financial Data:
- Market Cap: ${financial_data.get('market_cap', 0):,.0f}
- Revenue: ${financial_data.get('revenue', 0):,.0f}
- Profit Margin: {financial_data.get('profit_margin', 0):.2%}
- P/E Ratio: {financial_data.get('pe_ratio', 'N/A')}
- Current Price: ${financial_data.get('current_price', 0):.2f}
- 52-Week Range: ${financial_data.get('52_week_low', 0):.2f} - ${financial_data.get('52_week_high', 0):.2f}
- Uploaded Documents: {rag_text[:1000]}

Return ONLY a JSON object:
{{
    "key_highlights": [
        "Highlight 1: Valuation/market cap insight",
        "Highlight 2: Profitability/revenue trend",
        "Highlight 3: Financial health indicator",
        "Highlight 4: Growth/performance metric",
        "Highlight 5: Investment perspective (optional)"
    ]
}}

Each highlight should be ONE concise sentence. Focus on actionable financial insights.
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            task_type="reasoning",  # Use Llama 3.3 70B
            temperature=0.3,
            max_tokens=600  # Reduced
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
            logger.warning("financial_model_json_parse_failed")
            return {
                "key_highlights": [
                    f"Market cap: ${financial_data.get('market_cap', 0) / 1e9:.1f}B",
                    f"P/E ratio: {financial_data.get('pe_ratio', 'N/A')}",
                    f"Profit margin: {financial_data.get('profit_margin', 0):.1%}",
                    "Financial analysis unavailable"
                ]
            }
