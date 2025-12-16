"""Research Agent - Gathers comprehensive data for strategic analysis."""

import asyncio
import time
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.db_service import DatabaseService
from app.services.external_apis import ExternalDataService
from app.models.state import AgentState
from app.agents.prompts.research_prompts import (
    CONSOLIDATE_RESEARCH_PROMPT,
    IDENTIFY_COMPETITORS_PROMPT,
    EXTRACT_KEY_FACTS_PROMPT
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ResearchAgent:
    """
    Research Agent that gathers comprehensive data from multiple sources:
    - RAG (case studies, industry reports, financial templates)
    - Real news (NewsAPI or Google News RSS)
    - Real financial data (Yahoo Finance)
    - Company info (Wikipedia)
    - Market data (World Bank API)
    """
    
    def __init__(
        self,
        rag: RAGService,
        llm: LLMService,
        db: DatabaseService,
        external: ExternalDataService
    ):
        """
        Initialize Research Agent.
        
        Args:
            rag: RAG service for knowledge base queries
            llm: LLM service for analysis
            db: Database service for caching
            external: External data service for real-time data
        """
        self.rag = rag
        self.llm = llm
        self.db = db
        self.external = external
        self.name = "research_agent"
        
        logger.info("research_agent_initialized")
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Main execution method called by LangGraph.
        
        Full research pipeline:
        1. Check cache first
        2. Query RAG for relevant context
        3. Fetch live data in parallel
        4. Consolidate using LLM
        5. Store in cache and update state
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with research_data populated
        """
        try:
            request = state["request"]
            company = request["company_name"]
            industry = request["industry"]
            question = request["strategic_question"]
            
            logger.info(
                "research_agent_starting",
                company=company,
                industry=industry
            )
            
            # Step 1: Check cache
            cache_key = f"research:{company}:{industry}:{hashlib.md5(question.encode()).hexdigest()}"
            cached = await self.db.get_cached_data(cache_key)
            
            if cached:
                logger.info("cache_hit", cache_key=cache_key)
                state["research_data"] = cached
                state["rag_context"] = cached.get("rag_context", [])
                return state
            
            # Step 2: Parallel data gathering
            start_time = time.time()
            
            logger.info("starting_parallel_data_fetch")
            
            tasks = [
                self.gather_rag_context(question, company, industry),
                self.fetch_live_news(company, industry),
                self.fetch_financial_data(company),
                self.fetch_regulatory_info(industry, "global"),
                self.identify_competitors(company, industry)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            rag_context, news, financials, regulatory, competitors = results
            
            # Handle any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_msg = f"Research task {i} failed: {str(result)}"
                    state["errors"].append(error_msg)
                    logger.error("research_task_failed", task_index=i, error=str(result))
                    # Provide empty defaults
                    if i in [2, 3]:  # financials, regulatory
                        results[i] = {}
                    else:  # lists
                        results[i] = []
            
            rag_context, news, financials, regulatory, competitors = results
            
            # Step 3: Consolidate using LLM
            logger.info("consolidating_research")
            consolidated = await self.consolidate_research(
                rag_context, news, financials, regulatory, competitors, question
            )
            
            # Step 4: Update state
            state["research_data"] = consolidated
            state["rag_context"] = rag_context
            state["metadata"]["research_time"] = time.time() - start_time
            
            # Step 5: Cache results (24 hours)
            await self.db.cache_research_data(cache_key, consolidated, ttl=86400)
            
            # Step 6: Log execution
            await self.db.save_agent_log(
                agent_name=self.name,
                execution_time=state["metadata"]["research_time"],
                success=True,
                metadata={
                    "data_points": len(rag_context) + len(news),
                    "company": company,
                    "industry": industry
                }
            )
            
            logger.info(
                "research_agent_complete",
                execution_time=state["metadata"]["research_time"],
                data_points=len(rag_context) + len(news)
            )
            
            return state
            
        except Exception as e:
            error_msg = f"Research agent failed: {str(e)}"
            state["errors"].append(error_msg)
            logger.error("research_agent_failed", error=str(e))
            return state
    
    async def gather_rag_context(
        self,
        query: str,
        company: str,
        industry: str
    ) -> List[Dict[str, Any]]:
        """
        Query RAG for relevant context from knowledge base.
        
        Searches across:
        - Case studies (similar companies/situations)
        - Industry reports (market insights)
        - Financial templates (analysis frameworks)
        
        Args:
            query: Strategic question
            company: Company name
            industry: Industry name
            
        Returns:
            List of relevant documents with metadata
        """
        try:
            logger.info("gathering_rag_context", query=query[:50])
            
            # Search across all namespaces
            tasks = [
                self.rag.semantic_search(
                    query=f"{query} {company} {industry}",
                    namespace="case_studies",
                    top_k=5
                ),
                self.rag.semantic_search(
                    query=f"{industry} market analysis",
                    namespace="industry_reports",
                    top_k=3
                ),
                self.rag.semantic_search(
                    query="financial analysis framework",
                    namespace="financial_templates",
                    top_k=2
                )
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten results
            all_docs = []
            for result in results:
                if isinstance(result, list):
                    all_docs.extend(result)
            
            logger.info("rag_context_gathered", doc_count=len(all_docs))
            return all_docs
            
        except Exception as e:
            logger.error("rag_context_failed", error=str(e))
            return []
    
    async def fetch_live_news(
        self,
        company: str,
        industry: str,
        lookback_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent news using NewsAPI or Google News fallback.
        
        Args:
            company: Company name
            industry: Industry name
            lookback_days: Days to look back
            
        Returns:
            List of news articles
        """
        try:
            logger.info("fetching_live_news", company=company)
            
            from_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            
            # Fetch news for company and industry
            company_news = await self.external.fetch_news_articles(
                query=company,
                from_date=from_date,
                to_date=to_date,
                max_results=5
            )
            
            industry_news = await self.external.fetch_news_articles(
                query=industry,
                from_date=from_date,
                to_date=to_date,
                max_results=5
            )
            
            all_news = company_news + industry_news
            
            logger.info("news_fetched", count=len(all_news))
            return all_news
            
        except Exception as e:
            logger.error("news_fetch_failed", error=str(e))
            return []
    
    async def fetch_financial_data(self, company: str) -> Dict[str, Any]:
        """
        Fetch financial data from Yahoo Finance.
        
        Args:
            company: Company name (will attempt to find ticker)
            
        Returns:
            Financial data dictionary
        """
        try:
            logger.info("fetching_financial_data", company=company)
            
            # Try to get ticker (you may need a mapping service)
            # For now, try common patterns
            ticker = await self._company_to_ticker(company)
            
            if ticker:
                data = await self.external.fetch_company_financials(ticker)
                logger.info("financial_data_fetched", ticker=ticker)
                return data
            else:
                logger.warning("ticker_not_found", company=company)
                return {"company": company, "ticker": None}
                
        except Exception as e:
            logger.error("financial_data_failed", error=str(e))
            return {}
    
    async def _company_to_ticker(self, company: str) -> Optional[str]:
        """
        Convert company name to stock ticker.
        
        Common mappings for Indian companies:
        """
        ticker_map = {
            'zomato': 'ZOMATO.NS',
            'swiggy': 'SWIGGY.NS',
            'flipkart': 'FLIPKART.NS',
            'paytm': 'PAYTM.NS',
            'ola': 'OLA.NS',
            'tesla': 'TSLA',
            'apple': 'AAPL',
            'google': 'GOOGL',
            'microsoft': 'MSFT',
            'amazon': 'AMZN'
        }
        
        company_lower = company.lower()
        for key, ticker in ticker_map.items():
            if key in company_lower:
                return ticker
        
        return None
    
    async def fetch_regulatory_info(
        self,
        industry: str,
        target_region: str
    ) -> Dict[str, Any]:
        """
        Fetch regulatory context from RAG.
        
        Args:
            industry: Industry name
            target_region: Target geographic region
            
        Returns:
            Regulatory information
        """
        try:
            logger.info("fetching_regulatory_info", industry=industry)
            
            # Query RAG for regulatory information
            query = f"{industry} regulations compliance {target_region}"
            results = await self.rag.semantic_search(
                query=query,
                namespace="industry_reports",
                top_k=3
            )
            
            # Extract regulatory mentions
            regulations = []
            requirements = []
            
            for doc in results:
                text = doc.get('text', '')
                if 'regulat' in text.lower() or 'compliance' in text.lower():
                    regulations.append({
                        'source': doc.get('metadata', {}).get('source', ''),
                        'excerpt': text[:200]
                    })
            
            return {
                'regulations': regulations,
                'requirements': requirements,
                'restrictions': []
            }
            
        except Exception as e:
            logger.error("regulatory_info_failed", error=str(e))
            return {'regulations': [], 'requirements': [], 'restrictions': []}
    
    async def identify_competitors(
        self,
        company: str,
        industry: str
    ) -> List[Dict[str, Any]]:
        """
        Use LLM + RAG to identify competitors.
        
        Args:
            company: Company name
            industry: Industry name
            
        Returns:
            List of competitors with details
        """
        try:
            logger.info("identifying_competitors", company=company)
            
            # Get context from RAG
            context_docs = await self.rag.semantic_search(
                query=f"{industry} competitors market share",
                namespace="case_studies",
                top_k=5
            )
            
            context_text = "\n\n".join([
                f"{doc.get('metadata', {}).get('title', 'Document')}: {doc.get('text', '')[:500]}"
                for doc in context_docs
            ])
            
            # Use LLM to extract competitors
            prompt = IDENTIFY_COMPETITORS_PROMPT.format(
                company=company,
                industry=industry,
                context=context_text
            )
            
            response = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a competitive intelligence analyst.",
                response_schema=[]
            )
            
            logger.info("competitors_identified", count=len(response) if isinstance(response, list) else 0)
            return response if isinstance(response, list) else []
            
        except Exception as e:
            logger.error("competitor_identification_failed", error=str(e))
            return []
    
    async def consolidate_research(
        self,
        rag_context: List[Dict],
        news: List[Dict],
        financials: Dict,
        regulatory: Dict,
        competitors: List[Dict],
        question: str
    ) -> Dict[str, Any]:
        """
        Consolidate all research using LLM.
        
        Args:
            rag_context: Documents from RAG
            news: News articles
            financials: Financial data
            regulatory: Regulatory info
            competitors: Competitor list
            question: Strategic question
            
        Returns:
            Consolidated research data
        """
        try:
            logger.info("consolidating_research_data")
            
            # Format inputs for LLM
            rag_text = "\n\n".join([
                f"[{doc.get('metadata', {}).get('source', 'Unknown')}]: {doc.get('text', '')[:300]}"
                for doc in rag_context[:10]
            ])
            
            news_text = "\n\n".join([
                f"[{article.get('source', 'Unknown')} - {article.get('published_at', '')}]: {article.get('title', '')} - {article.get('summary', '')[:200]}"
                for article in news[:10]
            ])
            
            financials_text = json.dumps(financials, indent=2)
            regulatory_text = json.dumps(regulatory, indent=2)
            competitors_text = json.dumps(competitors, indent=2)
            
            # Generate consolidation prompt
            prompt = CONSOLIDATE_RESEARCH_PROMPT.format(
                rag_context=rag_text,
                news=news_text,
                financials=financials_text,
                regulatory=regulatory_text,
                competitors=competitors_text,
                strategic_question=question
            )
            
            # Call LLM
            consolidated = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a senior research analyst at McKinsey & Company.",
                response_schema={}
            )
            
            # Add metadata
            consolidated['timestamp'] = datetime.utcnow().isoformat()
            consolidated['rag_context'] = rag_context
            consolidated['news_highlights'] = news
            consolidated['financial_snapshot'] = financials
            consolidated['citations'] = [
                {'source': doc.get('metadata', {}).get('source', ''), 'type': 'rag'}
                for doc in rag_context
            ]
            
            logger.info("research_consolidated")
            return consolidated
            
        except Exception as e:
            logger.error("consolidation_failed", error=str(e))
            # Return basic structure on failure
            return {
                'key_findings': [],
                'market_context': {},
                'competitive_overview': {},
                'regulatory_summary': regulatory,
                'financial_snapshot': financials,
                'news_highlights': news,
                'data_quality': {
                    'completeness': 0.5,
                    'recency': 'moderate',
                    'reliability': 0.6,
                    'source_count': len(rag_context) + len(news)
                },
                'data_gaps': ['LLM consolidation failed'],
                'citations': [],
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def extract_key_facts(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract key facts from unstructured text.
        
        Args:
            text: Input text
            
        Returns:
            List of facts with confidence scores
        """
        try:
            prompt = EXTRACT_KEY_FACTS_PROMPT.format(text=text)
            
            facts = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a data analyst extracting facts.",
                response_schema=[]
            )
            
            return facts if isinstance(facts, list) else []
            
        except Exception as e:
            logger.error("fact_extraction_failed", error=str(e))
            return []
