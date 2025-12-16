"""
Automated Knowledge Base Ingestion for Stratagem AI

This script downloads and ingests documents from multiple sources:
- Consulting firm insights (McKinsey, BCG, Bain)
- Financial templates and models
- Industry reports
- Regulatory documents

Usage:
    python scripts/auto_ingest_knowledge.py --category all
    python scripts/auto_ingest_knowledge.py --category consulting
    python scripts/auto_ingest_knowledge.py --category financial
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict
import json
from datetime import datetime

from app.services.rag_service import RAGService
from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeBaseIngester:
    """Automated knowledge base ingestion from multiple sources."""
    
    def __init__(self):
        """Initialize ingester."""
        self.settings = get_settings()
        self.rag_service = None
        self.data_dir = Path("data/knowledge_base")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create category directories
        self.categories = {
            "consulting": self.data_dir / "consulting",
            "financial": self.data_dir / "financial",
            "industry": self.data_dir / "industry",
            "regulatory": self.data_dir / "regulatory"
        }
        
        for category_dir in self.categories.values():
            category_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize_rag(self):
        """Initialize RAG service."""
        self.rag_service = RAGService(
            api_key=self.settings.pinecone_api_key,
            environment=self.settings.pinecone_environment,
            index_name=self.settings.pinecone_index_name
        )
        await self.rag_service.connect()
        logger.info("RAG service initialized")
    
    def download_page_content(self, url: str, timeout: int = 10) -> str:
        """Download and extract text content from URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return ""
    
    async def ingest_consulting_insights(self):
        """Ingest consulting firm insights."""
        logger.info("Ingesting consulting insights...")
        
        sources = {
            "McKinsey": [
                "https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights",
                "https://www.mckinsey.com/industries/retail/our-insights",
                "https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights"
            ],
            "BCG": [
                "https://www.bcg.com/publications/collections/most-popular-articles",
                "https://www.bcg.com/capabilities/digital-technology-data/overview"
            ],
            "Bain": [
                "https://www.bain.com/insights/topics/mergers-acquisitions/",
                "https://www.bain.com/insights/topics/digital/"
            ],
            "HBR": [
                "https://hbr.org/topic/subject/strategy",
                "https://hbr.org/topic/subject/finance"
            ],
            "YC": [
                "https://www.ycombinator.com/blog/category/growth",
                "https://www.ycombinator.com/blog/category/fundraising"
            ],
            "a16z": [
                "https://a16z.com/category/fintech/",
                "https://a16z.com/category/enterprise/"
            ],
            "Blume": [
                "https://blume.vc/indusvalley"
            ]
        }
        
        documents = []
        
        for source, urls in sources.items():
            logger.info(f"Processing {source}...")
            
            for url in urls:
                try:
                    content = self.download_page_content(url)
                    
                    if content and len(content) > 500:
                        doc = {
                            "content": content[:10000],  # Limit to 10k chars
                            "source": source,
                            "url": url,
                            "category": "consulting",
                            "timestamp": datetime.now().isoformat()
                        }
                        documents.append(doc)
                        
                        # Save locally
                        filename = f"{source}_{url.split('/')[-1][:50]}.json"
                        filepath = self.categories["consulting"] / filename
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(doc, f, indent=2)
                        
                        logger.info(f"Downloaded: {source} - {url}")
                    
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    continue
        
        logger.info(f"Consulting insights: {len(documents)} documents collected")
        return documents
    
    async def ingest_financial_templates(self):
        """Ingest financial analysis templates and guides."""
        logger.info("Ingesting financial templates...")
        
        sources = {
            "WSP": [
                "https://www.wallstreetprep.com/knowledge/dcf-model/",
                "https://www.wallstreetprep.com/knowledge/valuation-methods/"
            ],
            "CFI": [
                "https://corporatefinanceinstitute.com/resources/valuation/dcf-formula-guide/",
                "https://corporatefinanceinstitute.com/resources/financial-modeling/financial-modeling-best-practices/"
            ],
            "Damodaran": [
                "http://pages.stern.nyu.edu/~adamodar/New_Home_Page/valuation.html"
            ],
            "Investopedia": [
                "https://www.investopedia.com/terms/d/dcf.asp",
                "https://www.investopedia.com/terms/l/ltv-ratio.asp",
                "https://www.investopedia.com/terms/c/cac.asp"
            ]
        }
        
        documents = []
        
        for source, urls in sources.items():
            logger.info(f"Processing {source}...")
            
            for url in urls:
                try:
                    content = self.download_page_content(url)
                    
                    if content and len(content) > 500:
                        doc = {
                            "content": content[:10000],
                            "source": source,
                            "url": url,
                            "category": "financial",
                            "timestamp": datetime.now().isoformat()
                        }
                        documents.append(doc)
                        
                        # Save locally
                        filename = f"{source}_{url.split('/')[-1][:50]}.json"
                        filepath = self.categories["financial"] / filename
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(doc, f, indent=2)
                        
                        logger.info(f"Downloaded: {source} - {url}")
                    
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    continue
        
        logger.info(f"Financial templates: {len(documents)} documents collected")
        return documents
    
    async def ingest_industry_reports(self):
        """Ingest industry reports and market data."""
        logger.info("Ingesting industry reports...")
        
        sources = {
            "Statista": [
                "https://www.statista.com/markets/",
                "https://www.statista.com/topics/"
            ],
            "NASSCOM": [
                "https://nasscom.in/knowledge-center"
            ],
            "Inc42": [
                "https://inc42.com/reports/"
            ],
            "RedSeer": [
                "https://redseer.com/reports/"
            ]
        }
        
        documents = []
        
        for source, urls in sources.items():
            logger.info(f"Processing {source}...")
            
            for url in urls:
                try:
                    content = self.download_page_content(url)
                    
                    if content and len(content) > 500:
                        doc = {
                            "content": content[:10000],
                            "source": source,
                            "url": url,
                            "category": "industry",
                            "timestamp": datetime.now().isoformat()
                        }
                        documents.append(doc)
                        
                        # Save locally
                        filename = f"{source}_{url.split('/')[-1][:50]}.json"
                        filepath = self.categories["industry"] / filename
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(doc, f, indent=2)
                        
                        logger.info(f"Downloaded: {source} - {url}")
                    
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    continue
        
        logger.info(f"Industry reports: {len(documents)} documents collected")
        return documents
    
    async def ingest_regulatory_docs(self):
        """Ingest regulatory and compliance documents."""
        logger.info("Ingesting regulatory documents...")
        
        sources = {
            "InvestIndia": [
                "https://www.investindia.gov.in/sector"
            ],
            "WorldBank": [
                "https://archive.doingbusiness.org/en/rankings"
            ],
            "UNCTAD": [
                "https://investmentpolicy.unctad.org/"
            ],
            "EY": [
                "https://www.ey.com/en_gl/tax-guides"
            ],
            "WTO": [
                "https://www.wto.org/english/tratop_e/tariffs_e/tariff_data_e.htm"
            ]
        }
        
        documents = []
        
        for source, urls in sources.items():
            logger.info(f"Processing {source}...")
            
            for url in urls:
                try:
                    content = self.download_page_content(url)
                    
                    if content and len(content) > 500:
                        doc = {
                            "content": content[:10000],
                            "source": source,
                            "url": url,
                            "category": "regulatory",
                            "timestamp": datetime.now().isoformat()
                        }
                        documents.append(doc)
                        
                        # Save locally
                        filename = f"{source}_{url.split('/')[-1][:50]}.json"
                        filepath = self.categories["regulatory"] / filename
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(doc, f, indent=2)
                        
                        logger.info(f"Downloaded: {source} - {url}")
                    
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    continue
        
        logger.info(f"Regulatory docs: {len(documents)} documents collected")
        return documents
    
    async def ingest_documents_to_pinecone(self, documents: List[Dict]):
        """Ingest documents into Pinecone with proper namespaces."""
        logger.info(f"Ingesting {len(documents)} documents to Pinecone...")
        
        # Map categories to namespaces
        namespace_map = {
            "consulting": "case_studies",
            "financial": "financial_templates",
            "industry": "industry_reports",
            "regulatory": "regulations"
        }
        
        for i, doc in enumerate(documents):
            try:
                # Get namespace from category
                category = doc.get("category", "general")
                namespace = namespace_map.get(category, "default")
                
                # Create chunks (max 1000 chars each)
                content = doc["content"]
                chunk_size = 1000
                chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                
                for chunk_idx, chunk in enumerate(chunks):
                    metadata = {
                        "source": doc["source"],
                        "category": doc["category"],
                        "url": doc["url"],
                        "chunk": chunk_idx,
                        "timestamp": doc["timestamp"]
                    }
                    
                    # Ingest to Pinecone with proper namespace
                    await self.rag_service.ingest_document(
                        text=chunk,
                        metadata=metadata,
                        namespace=namespace
                    )
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Ingested {i + 1}/{len(documents)} documents")
                
            except Exception as e:
                logger.error(f"Failed to ingest document {i}: {e}")
                continue
        
        logger.info("Pinecone ingestion complete!")
    
    async def run(self, category: str = "all"):
        """Run ingestion for specified category."""
        await self.initialize_rag()
        
        all_documents = []
        
        if category in ["all", "consulting"]:
            docs = await self.ingest_consulting_insights()
            all_documents.extend(docs)
        
        if category in ["all", "financial"]:
            docs = await self.ingest_financial_templates()
            all_documents.extend(docs)
        
        if category in ["all", "industry"]:
            docs = await self.ingest_industry_reports()
            all_documents.extend(docs)
        
        if category in ["all", "regulatory"]:
            docs = await self.ingest_regulatory_docs()
            all_documents.extend(docs)
        
        # Ingest to Pinecone
        if all_documents:
            await self.ingest_documents_to_pinecone(all_documents)
        
        logger.info(f"Total documents collected: {len(all_documents)}")
        logger.info(f"Data saved to: {self.data_dir}")


async def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated knowledge base ingestion")
    parser.add_argument(
        "--category",
        choices=["all", "consulting", "financial", "industry", "regulatory"],
        default="all",
        help="Category to ingest"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("STRATAGEM AI - KNOWLEDGE BASE INGESTION")
    print("="*80 + "\n")
    print(f"Category: {args.category}")
    print(f"This will download and ingest documents from multiple sources...")
    print("\nPress Ctrl+C to cancel\n")
    
    time.sleep(3)
    
    ingester = KnowledgeBaseIngester()
    await ingester.run(category=args.category)
    
    print("\n" + "="*80)
    print("INGESTION COMPLETE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
