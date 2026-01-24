"""External APIs service for news, financial data, and web scraping."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import httpx
from bs4 import BeautifulSoup
import wikipediaapi
from app.services.cache_service import CacheService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ExternalDataService:
    """
    Service for fetching data from external APIs.
    
    Data sources:
    - Yahoo Finance (financial data) - FREE
    - Google News RSS (news) - FREE
    - Wikipedia (company background) - FREE
    - Web scraping (fallback) - FREE
    """
    
    def __init__(self, cache: CacheService, newsapi_key: Optional[str] = None):
        self.cache = cache
        self.newsapi_key = newsapi_key
        self.wiki = wikipediaapi.Wikipedia('OriginLabs/1.0', 'en')
        
        logger.info("external_data_service_initialized")
    
    async def fetch_wikipedia(self, company: str) -> Dict[str, Any]:
        """
        Fetch company information from Wikipedia.
        
        Args:
            company: Company name
        
        Returns:
            Dictionary with summary and metadata
        """
        # Check cache
        cached = await self.cache.get_api_response("wikipedia", {"company": company})
        if cached:
            return cached
        
        try:
            page = self.wiki.page(company)
            
            if page.exists():
                result = {
                    "title": page.title,
                    "summary": page.summary[:1000],  # First 1000 chars
                    "url": page.fullurl,
                    "exists": True
                }
            else:
                result = {
                    "exists": False,
                    "summary": ""
                }
            
            # Cache for 7 days
            await self.cache.cache_api_response(
                "wikipedia",
                {"company": company},
                result,
                ttl=604800
            )
            
            logger.info("wikipedia_fetch_success", company=company)
            return result
            
        except Exception as e:
            logger.error("wikipedia_fetch_failed", company=company, error=str(e))
            return {"exists": False, "summary": ""}
    
    async def fetch_financial_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch financial data from Yahoo Finance.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Financial data dictionary
        """
        # Check cache (1 hour TTL)
        cached = await self.cache.get_api_response("yfinance", {"ticker": ticker})
        if cached:
            return cached
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get historical data (1 year)
            hist = stock.history(period="1y")
            
            # Convert historical data to dict with string keys for MongoDB
            historical_dict = {}
            if not hist.empty:
                for col in hist.columns:
                    historical_dict[col] = {
                        str(date): float(value) if not pd.isna(value) else None
                        for date, value in hist[col].items()
                    }
            
            result = {
                "ticker": ticker,
                "company_name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", 0),
                "revenue": info.get("totalRevenue", 0),
                "profit_margin": info.get("profitMargins", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "current_price": info.get("currentPrice", 0),
                "52_week_high": info.get("fiftyTwoWeekHigh", 0),
                "52_week_low": info.get("fiftyTwoWeekLow", 0),
                "historical_prices": historical_dict
            }
            
            # Cache for 1 hour
            await self.cache.cache_api_response(
                "yfinance",
                {"ticker": ticker},
                result,
                ttl=3600
            )
            
            logger.info("yfinance_fetch_success", ticker=ticker)
            return result
            
        except Exception as e:
            logger.error("yfinance_fetch_failed", ticker=ticker, error=str(e))
            return {}
    
    async def fetch_recent_news(
        self,
        company: str,
        limit: int = 10,
        lookback_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent news about a company.
        
        Uses Google News RSS (free) as primary source.
        
        Args:
            company: Company name
            limit: Maximum number of articles
            lookback_days: Days to look back
        
        Returns:
            List of news articles
        """
        # Check cache (24 hour TTL)
        cache_key = {"company": company, "limit": limit}
        cached = await self.cache.get_api_response("news", cache_key)
        if cached:
            return cached
        
        try:
            articles = await self._fetch_google_news_rss(company, limit)
            
            # Cache for 24 hours
            await self.cache.cache_api_response(
                "news",
                cache_key,
                articles,
                ttl=86400
            )
            
            logger.info(
                "news_fetch_success",
                company=company,
                count=len(articles)
            )
            return articles
            
        except Exception as e:
            logger.error("news_fetch_failed", company=company, error=str(e))
            return []
    
    async def _fetch_google_news_rss(
        self,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch news from Google News RSS feed."""
        try:
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
            
            # Parse RSS feed
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:limit]
            
            articles = []
            for item in items:
                articles.append({
                    "title": item.title.text if item.title else "",
                    "link": item.link.text if item.link else "",
                    "published": item.pubDate.text if item.pubDate else "",
                    "source": "Google News"
                })
            
            return articles
            
        except Exception as e:
            logger.error("google_news_rss_failed", query=query, error=str(e))
            return []
    
    def company_to_ticker(self, company: str) -> Optional[str]:
        """
        Convert company name to stock ticker.
        
        Simple mapping for common companies.
        """
        ticker_map = {
            # US Companies
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "meta": "META",
            "facebook": "META",
            "tesla": "TSLA",
            "nvidia": "NVDA",
            "netflix": "NFLX",
            
            # Indian Companies
            "reliance": "RELIANCE.NS",
            "tcs": "TCS.NS",
            "infosys": "INFY.NS",
            "hdfc bank": "HDFCBANK.NS",
            "icici bank": "ICICIBANK.NS",
            "wipro": "WIPRO.NS",
            "bharti airtel": "BHARTIARTL.NS",
            "itc": "ITC.NS",
            "sbi": "SBIN.NS",
            "adani": "ADANIENT.NS"
        }
        
        company_lower = company.lower()
        
        # Direct match
        if company_lower in ticker_map:
            return ticker_map[company_lower]
        
        # Partial match
        for key, ticker in ticker_map.items():
            if key in company_lower or company_lower in key:
                return ticker
        
        # Try as-is (might be ticker already)
        return company.upper()
