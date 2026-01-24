"""Market Research Agent - Analyzes market landscape and competitors."""

import asyncio
from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.models.state import AgentState
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MarketResearchAgent(BaseAgent):
    """
    Agent 2: Market & Competitor Research
    
    Responsibilities:
    - Analyze market size and trends
    - Identify top competitors
    - Competitive positioning analysis
    - Industry dynamics
    
    Data Sources:
    - RAG (industry reports, market data)
    - LLM reasoning
    
    Model: Llama 3.3 70B (complex reasoning required)
    
    Note: This agent can run in parallel with Financial and Risk agents
    """
    
    def __init__(
        self,
        llm: LLMService,
        rag: RAGService
    ):
        super().__init__("market_research")
        self.llm = llm
        self.rag = rag
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute market research and competitor analysis.
        
        Args:
            state: Current agent state with 'company_profile'
        
        Returns:
            State with 'market_analysis' and 'competitor_analysis' populated
        """
        # Validate input
        if not self._validate_state(state, ["company_profile"]):
            return state
        
        company_name = state["company_profile"]["name"]
        industry = state["company_profile"].get("industry", "Unknown")
        
        logger.info("analyzing_market", company=company_name, industry=industry)
        
        # Run market analysis and competitor identification in parallel
        market_data, competitor_data = await asyncio.gather(
            self._analyze_market(industry, state),
            self._identify_competitors(company_name, industry)
        )
        
        # Update state
        state["market_analysis"] = market_data
        state["competitor_analysis"] = competitor_data
        
        logger.info(
            "market_research_completed",
            company=company_name,
            competitors_found=len(competitor_data)
        )
        
        return state
    
    async def _analyze_market(self, industry: str, state: AgentState = None) -> Dict[str, Any]:
        """Analyze market size, trends, and dynamics."""
        
        # Query RAG for industry reports
        rag_context = await self.rag.query(
            query_text=f"market analysis trends {industry}",
            top_k=3,
            filter={"type": "industry_report"} if industry != "Unknown" else None
        )
        
        # Build context from RAG results
        context_text = "\n".join([
            f"- {doc['text'][:300]}" for doc in rag_context
        ]) if rag_context else "No industry reports available"
        
        # Check for dynamic prompt from Intent Analyzer
        dynamic_prompts = state.get("dynamic_prompts", {}) if state else {}
        custom_prompt = dynamic_prompts.get("market_research")
        
        if custom_prompt:
            # Use MBB-grade Porter's 5 Forces prompt
            logger.info("using_dynamic_prompt", agent="market_research")
            
            prompt = f"""{custom_prompt}

Available Context:
{context_text}

Return ONLY a JSON object:
{{
    "market_size_billions": estimated_size or null,
    "growth_rate_percent": estimated_cagr or null,
    "key_insights": [
        "Insight 1: Porter's 5 Forces analysis point",
        "Insight 2: Competitive dynamics insight",
        "Insight 3: Market attractiveness factor",
        "Insight 4: Strategic implication"
    ]
}}

Focus on competitive dynamics using Porter's 5 Forces framework. Be specific with data.
"""
        else:
            # Fallback to default prompt
            logger.info("using_default_prompt", agent="market_research")
            
            prompt = f"""Analyze the {industry} market and provide 4-5 KEY INSIGHTS as bullet points.

Available Context:
{context_text}

Return ONLY a JSON object:
{{
    "market_size_billions": estimated_size or null,
    "growth_rate_percent": estimated_cagr or null,
    "key_insights": [
        "Insight 1: Brief, data-driven statement",
        "Insight 2: Brief, data-driven statement",
        "Insight 3: Brief, data-driven statement",
        "Insight 4: Brief, data-driven statement"
    ]
}}

Focus on market size, growth trends, and key dynamics. Keep insights concise.
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            task_type="reasoning",  # Use Llama 3.3 70B
            temperature=0.3,
            max_tokens=600  # Reduced for concise output
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
            logger.warning("market_analysis_json_parse_failed")
            return {
                "key_insights": [
                    f"{industry} market analysis unavailable"
                ]
            }
    
    async def _identify_competitors(
        self,
        company_name: str,
        industry: str
    ) -> List[Dict[str, Any]]:
        """Identify and analyze top competitors."""
        
        # Query RAG for competitor information
        rag_context = await self.rag.query(
            query_text=f"competitors {company_name} {industry}",
            top_k=3
        )
        
        context_text = "\n".join([
            f"- {doc['text'][:200]}" for doc in rag_context
        ]) if rag_context else "No competitor data available"
        
        # LLM analysis
        prompt = f"""Identify the TOP 3-4 COMPETITORS for {company_name} in {industry}.

Context:
{context_text}

Return ONLY a JSON object:
{{
    "competitors": [
        {{
            "name": "Competitor 1",
            "key_point": "One sentence: position + main strength/weakness"
        }},
        {{
            "name": "Competitor 2",
            "key_point": "One sentence: position + main strength/weakness"
        }},
        {{
            "name": "Competitor 3",
            "key_point": "One sentence: position + main strength/weakness"
        }}
    ]
}}

Keep each key_point to ONE concise sentence. Focus on competitive positioning.
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            task_type="reasoning",
            temperature=0.3,
            max_tokens=500  # Reduced
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
            
            return data.get("competitors", [])
            
        except (json.JSONDecodeError, Exception):
            logger.warning("competitor_analysis_json_parse_failed")
            return []
