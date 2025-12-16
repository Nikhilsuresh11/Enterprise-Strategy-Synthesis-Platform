"""External data fetching service using REAL FREE APIs."""

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import httpx

# Real data libraries
import yfinance as yf
from newsapi import NewsApiClient
import wikipediaapi

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ExternalDataService:
    """
    Fetches real data from free, open-source APIs:
    - News: NewsAPI.org (100 requests/day free)
    - Financial: Yahoo Finance (yfinance - unlimited, free)
    - Company Info: Wikipedia API (unlimited, free)
    - Market Data: World Bank API (unlimited, free)
    """
    
    def __init__(self, newsapi_key: Optional[str] = None):
        """
        Initialize external data service.
        
        Args:
            newsapi_key: NewsAPI key (optional, get free at newsapi.org)
        """
        self.newsapi_key = newsapi_key
        self.newsapi_client = NewsApiClient(api_key=newsapi_key) if newsapi_key else None
        self.wiki = wikipediaapi.Wikipedia('Stratagem-AI/1.0', 'en')
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info("external_data_service_initialized", has_newsapi=bool(newsapi_key))
    
    async def fetch_news_articles(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = "en",
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch real news articles using NewsAPI.
        
        Args:
            query: Search query (company name, industry, etc.)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            language: Language code
            max_results: Maximum articles to return
            
        Returns:
            List of news articles with title, description, url, date, source
        """
        if not self.newsapi_client:
            logger.warning("newsapi_not_configured", query=query)
            return await self._fetch_news_fallback(query, max_results)
        
        try:
            # Default date range: last 30 days
            if not from_date:
                from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not to_date:
                to_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info("fetching_news", query=query, from_date=from_date, to_date=to_date)
            
            # Call NewsAPI (synchronous, so run in executor)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.newsapi_client.get_everything(
                    q=query,
                    from_param=from_date,
                    to=to_date,
                    language=language,
                    sort_by='relevancy',
                    page_size=max_results
                )
            )
            
            articles = []
            for article in response.get('articles', [])[:max_results]:
                articles.append({
                    'title': article.get('title', ''),
                    'summary': article.get('description', ''),
                    'content': article.get('content', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'relevance_score': 0.8  # NewsAPI doesn't provide this
                })
            
            logger.info("news_fetched", count=len(articles))
            return articles
            
        except Exception as e:
            logger.error("news_fetch_failed", error=str(e))
            return await self._fetch_news_fallback(query, max_results)
    
    async def _fetch_news_fallback(self, query: str, max_results: int) -> List[Dict]:
        """Fallback: Scrape Google News RSS (free, no API key needed)."""
        try:
            # Google News RSS feed
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            
            response = await self.http_client.get(url)
            
            if response.status_code == 200:
                # Parse RSS feed (simplified)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'xml')
                items = soup.find_all('item')[:max_results]
                
                articles = []
                for item in items:
                    articles.append({
                        'title': item.find('title').text if item.find('title') else '',
                        'summary': item.find('description').text if item.find('description') else '',
                        'url': item.find('link').text if item.find('link') else '',
                        'published_at': item.find('pubDate').text if item.find('pubDate') else '',
                        'source': 'Google News',
                        'relevance_score': 0.7
                    })
                
                logger.info("news_fetched_fallback", count=len(articles))
                return articles
        
        except Exception as e:
            logger.error("news_fallback_failed", error=str(e))
            return []
    
    async def fetch_company_financials(self, company_ticker: str) -> Dict[str, Any]:
        """
        Fetch real financial data using Yahoo Finance (FREE, unlimited).
        
        Args:
            company_ticker: Stock ticker symbol (e.g., "ZOMATO.NS" for NSE)
            
        Returns:
            Financial data including revenue, market cap, metrics
        """
        try:
            logger.info("fetching_financials", ticker=company_ticker)
            
            # Run yfinance in executor (it's synchronous)
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, company_ticker)
            
            # Get company info
            info = await loop.run_in_executor(None, lambda: ticker.info)
            
            # Get historical data for revenue trend
            financials = await loop.run_in_executor(None, lambda: ticker.financials)
            
            # Extract key metrics
            data = {
                'ticker': company_ticker,
                'company_name': info.get('longName', ''),
                'market_cap': info.get('marketCap', 0),
                'revenue': info.get('totalRevenue', 0),
                'employees': info.get('fullTimeEmployees', 0),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'website': info.get('website', ''),
                'description': info.get('longBusinessSummary', ''),
                'metrics': {
                    'gross_margin': info.get('grossMargins', 0),
                    'operating_margin': info.get('operatingMargins', 0),
                    'profit_margin': info.get('profitMargins', 0),
                    'roe': info.get('returnOnEquity', 0),
                    'debt_to_equity': info.get('debtToEquity', 0),
                    'current_ratio': info.get('currentRatio', 0),
                    'pe_ratio': info.get('trailingPE', 0)
                },
                'price_data': {
                    'current_price': info.get('currentPrice', 0),
                    'day_high': info.get('dayHigh', 0),
                    'day_low': info.get('dayLow', 0),
                    '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                    '52_week_low': info.get('fiftyTwoWeekLow', 0)
                }
            }
            
            logger.info("financials_fetched", ticker=company_ticker)
            return data
            
        except Exception as e:
            logger.error("financials_fetch_failed", ticker=company_ticker, error=str(e))
            return {
                'ticker': company_ticker,
                'error': str(e),
                'market_cap': 0,
                'revenue': 0
            }
    
    async def fetch_company_info(self, company_name: str) -> Dict[str, Any]:
        """
        Fetch company information from Wikipedia (FREE, unlimited).
        
        Args:
            company_name: Company name
            
        Returns:
            Company overview, history, operations
        """
        try:
            logger.info("fetching_wikipedia", company=company_name)
            
            # Run Wikipedia API in executor
            loop = asyncio.get_event_loop()
            page = await loop.run_in_executor(None, self.wiki.page, company_name)
            
            if not page.exists():
                logger.warning("wikipedia_page_not_found", company=company_name)
                return {'summary': '', 'url': ''}
            
            data = {
                'title': page.title,
                'summary': page.summary[:1000],  # First 1000 chars
                'url': page.fullurl,
                'categories': list(page.categories.keys())[:10]
            }
            
            logger.info("wikipedia_fetched", company=company_name)
            return data
            
        except Exception as e:
            logger.error("wikipedia_fetch_failed", company=company_name, error=str(e))
            return {'summary': '', 'url': ''}
    
    async def fetch_market_data(self, industry: str, region: str = "global") -> Dict[str, Any]:
        """
        Fetch market data from World Bank API (FREE, unlimited).
        
        Args:
            industry: Industry name
            region: Geographic region
            
        Returns:
            Market size, growth rate, economic indicators
        """
        try:
            logger.info("fetching_market_data", industry=industry, region=region)
            
            # World Bank API for economic indicators
            # Example: GDP growth, population, etc.
            country_code = self._region_to_country_code(region)
            
            url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.KD.ZG?format=json&date=2020:2023"
            
            response = await self.http_client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract GDP growth rates
                growth_rates = []
                if len(data) > 1:
                    for entry in data[1]:
                        if entry.get('value'):
                            growth_rates.append(entry['value'])
                
                avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
                
                return {
                    'region': region,
                    'gdp_growth_rate': avg_growth / 100,  # Convert to decimal
                    'data_source': 'World Bank',
                    'years': '2020-2023'
                }
            
            return {'region': region, 'gdp_growth_rate': 0.05}  # Default 5%
            
        except Exception as e:
            logger.error("market_data_fetch_failed", error=str(e))
            return {'region': region, 'gdp_growth_rate': 0.05}
    
    def _region_to_country_code(self, region: str) -> str:
        """Map region names to World Bank country codes."""
        mapping = {
            'global': 'WLD',
            'india': 'IND',
            'uae': 'ARE',
            'saudi arabia': 'SAU',
            'middle east': 'MEA',
            'usa': 'USA',
            'china': 'CHN'
        }
        return mapping.get(region.lower(), 'WLD')
    
    async def parallel_fetch(self, tasks: List) -> List[Any]:
        """
        Execute multiple fetch operations in parallel.
        
        Args:
            tasks: List of coroutines to execute
            
        Returns:
            List of results (exceptions returned as-is)
        """
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
