"""Company Profiling Agent - Gathers basic company information."""

from typing import Dict, Any
from app.agents.base import BaseAgent
from app.models.state import AgentState
from app.services.llm_service import LLMService
from app.services.external_apis import ExternalDataService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CompanyProfilingAgent(BaseAgent):
    """
    Agent 1: Company Profiling
    
    Responsibilities:
    - Gather basic company information
    - Fetch company background from Wikipedia
    - Get recent news highlights
    - Structure company profile
    
    Data Sources:
    - Wikipedia (company background)
    - Google News RSS (recent news)
    - Yahoo Finance (basic financial info)
    
    Model: Llama 3 8B (fast extraction task)
    """
    
    def __init__(
        self,
        llm: LLMService,
        external: ExternalDataService
    ):
        super().__init__("company_profiling")
        self.llm = llm
        self.external = external
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute company profiling.
        
        Args:
            state: Current agent state with 'request' field
        
        Returns:
            State with 'company_profile' populated
        """
        # Validate input
        if not self._validate_state(state, ["request"]):
            return state
        
        company_name = state["request"]["company_name"]
        industry = state["request"].get("industry", "")
        
        logger.info("profiling_company", company=company_name)
        
        # Gather data from multiple sources
        wiki_data = await self.external.fetch_wikipedia(company_name)
        news_data = await self.external.fetch_recent_news(company_name, limit=5)
        
        # Try to get ticker and basic financial info
        ticker = self.external.company_to_ticker(company_name)
        financial_data = {}
        if ticker:
            financial_data = await self.external.fetch_financial_data(ticker)
        
        # Use LLM to structure profile
        profile = await self._structure_profile(
            company_name=company_name,
            industry=industry,
            wiki_data=wiki_data,
            news_data=news_data,
            financial_data=financial_data,
            state=state
        )
        
        # Update state
        state["company_profile"] = profile
        
        logger.info(
            "company_profile_created",
            company=company_name,
            has_wiki=wiki_data.get("exists", False),
            news_count=len(news_data),
            has_financials=bool(financial_data)
        )
        
        return state
    
    async def _structure_profile(
        self,
        company_name: str,
        industry: str,
        wiki_data: Dict[str, Any],
        news_data: list,
        financial_data: Dict[str, Any],
        state: AgentState = None
    ) -> Dict[str, Any]:
        """Use LLM to structure company profile from raw data."""
        
        dynamic_prompts = state.get("dynamic_prompts", {}) if state else {}
        custom_prompt = dynamic_prompts.get("company_profiling")
        
        # Format RAG context
        rag_context = state.get("rag_context", []) if state else []
        rag_text = "\n".join(rag_context[:3]) if rag_context else "No uploaded documents"
        
        if custom_prompt:
            # Use MBB-grade dynamic prompt with framework
            logger.info("using_dynamic_prompt", agent="company_profiling")
            
            prompt = f"""{custom_prompt}

- Industry: {industry or "Unknown"}
- Wikipedia: {wiki_data.get("summary", "N/A")[:500]}
- Recent News: {self._format_news(news_data)}
- Financials: {self._format_financials(financial_data)}
- Uploaded Documents: {rag_text[:1000]}

Return ONLY a JSON object with these fields:
{{
    "name": "{company_name}",
    "industry": "Primary industry",
    "key_facts": [
        "Fact 1: Brief, impactful statement based on value chain analysis",
        "Fact 2: Brief, impactful statement",
        "Fact 3: Brief, impactful statement",
        "Fact 4: Brief, impactful statement"
    ],
    "ticker": "{financial_data.get('ticker', '')}" or null,
    "market_cap_billions": {financial_data.get('market_cap', 0) / 1e9:.1f} or null
}}

Keep each fact to ONE concise sentence. Focus on strategic value drivers and competitive moats.
"""
        else:
            # Fallback to default prompt
            logger.info("using_default_prompt", agent="company_profiling")
            
            prompt = f"""Analyze {company_name} and provide 4-5 KEY FACTS as bullet points.

- Industry: {industry or "Unknown"}
- Wikipedia: {wiki_data.get("summary", "N/A")[:300]}
- Recent News: {self._format_news(news_data)}
- Financials: {self._format_financials(financial_data)}
- Uploaded Documents: {rag_text[:1000]}

Return ONLY a JSON object with these fields:
{{
    "name": "{company_name}",
    "industry": "Primary industry",
    "key_facts": [
        "Fact 1: Brief, impactful statement",
        "Fact 2: Brief, impactful statement", 
        "Fact 3: Brief, impactful statement",
        "Fact 4: Brief, impactful statement"
    ],
    "ticker": "{financial_data.get('ticker', '')}" or null,
    "market_cap_billions": {financial_data.get('market_cap', 0) / 1e9:.1f} or null
}}

Keep each fact to ONE concise sentence. Focus on what makes this company notable.
"""
        
        # Call LLM (use fast model for extraction)
        response = await self.llm.generate(
            prompt=prompt,
            task_type="extraction",  # Will use Llama 3.1 8B
            temperature=0.1,
            max_tokens=500  # Reduced for concise output
        )
        
        # Parse JSON response
        try:
            import json
            import re
            
            # Try to extract JSON
            try:
                profile = json.loads(response)
            except json.JSONDecodeError:
                # Try to find JSON in response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    profile = json.loads(json_match.group(0))
                else:
                    raise
            
            return profile
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("llm_response_not_json", error=str(e))
            # Return basic profile with concise format
            return {
                "name": company_name,
                "industry": industry or "Unknown",
                "key_facts": [
                    news["title"] for news in news_data[:4]
                ] if news_data else ["Limited information available"],
                "ticker": financial_data.get("ticker"),
                "market_cap_billions": financial_data.get("market_cap", 0) / 1e9 if financial_data.get("market_cap") else None
            }
    
    def _format_news(self, news_data: list) -> str:
        """Format news data for prompt."""
        if not news_data:
            return "No recent news available"
        
        formatted = []
        for i, article in enumerate(news_data[:5], 1):
            formatted.append(f"{i}. {article.get('title', 'No title')}")
        
        return "\n".join(formatted)
    
    def _format_financials(self, financial_data: Dict[str, Any]) -> str:
        """Format financial data for prompt."""
        if not financial_data:
            return "No financial data available"
        
        return f"""
- Ticker: {financial_data.get('ticker', 'N/A')}
- Sector: {financial_data.get('sector', 'N/A')}
- Market Cap: ${financial_data.get('market_cap', 0):,.0f}
- Revenue: ${financial_data.get('revenue', 0):,.0f}
- P/E Ratio: {financial_data.get('pe_ratio', 'N/A')}
"""
