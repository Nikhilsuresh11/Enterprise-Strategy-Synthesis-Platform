"""Regulatory & Geopolitical Agent - Compliance and risk analysis."""

import asyncio
import time
import json
import re
from typing import Dict, Any, List, Optional

from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.db_service import DatabaseService
from app.services.regulatory_data import RegulatoryDataService
from app.models.state import AgentState
from app.agents.prompts.regulatory_prompts import (
    FDI_ANALYSIS_PROMPT,
    GEOPOLITICAL_RISK_PROMPT,
    REGULATORY_RISK_MATRIX_PROMPT,
    LEGAL_STRUCTURE_PROMPT,
    SECTOR_REGULATIONS_PROMPT
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RegulatoryAgent:
    """
    Regulatory & Geopolitical Agent performs compliance and risk analysis:
    - FDI regulations
    - Sector-specific regulations
    - Tax implications
    - Geopolitical risk assessment
    - Trade barriers
    - Labor regulations
    - Risk matrix generation
    - Legal structure recommendations
    """
    
    def __init__(self, llm: LLMService, rag: RAGService, db: DatabaseService):
        """
        Initialize Regulatory Agent.
        
        Args:
            llm: LLM service for analysis
            rag: RAG service for regulatory knowledge
            db: Database service for logging
        """
        self.llm = llm
        self.rag = rag
        self.db = db
        self.regulatory_data = RegulatoryDataService()
        self.name = "regulatory_agent"
        
        logger.info("regulatory_agent_initialized")
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Main execution: performs all regulatory and geopolitical analysis.
        
        Args:
            state: Current agent state with research_data
            
        Returns:
            Updated state with regulatory_findings
        """
        try:
            request = state["request"]
            research_data = state.get("research_data", {})
            
            logger.info(
                "regulatory_agent_starting",
                company=request["company_name"],
                industry=request["industry"]
            )
            
            start_time = time.time()
            
            # Extract countries from strategic question
            source_country = self._extract_source_country(request)
            target_country = self._extract_target_country(request["strategic_question"])
            
            logger.info(
                "countries_identified",
                source=source_country,
                target=target_country
            )
            
            # Run all analyses in parallel for speed
            logger.info("running_parallel_regulatory_analysis")
            
            tasks = [
                self.assess_fdi_regulations(
                    source_country, target_country,
                    request["industry"], json.dumps(research_data)[:1000]
                ),
                self.evaluate_sector_regulations(
                    request["industry"], target_country, "B2C"
                ),
                self.analyze_tax_implications(
                    "subsidiary", [source_country, target_country]
                ),
                self.assess_geopolitical_risk(
                    target_country, request["industry"],
                    json.dumps(research_data)[:1000]
                ),
                self.evaluate_trade_barriers(
                    source_country, target_country, request["industry"]
                ),
                self.assess_labor_regulations(target_country, request["industry"])
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            fdi, sector_reg, tax, geopolitical, trade, labor = results
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_msg = f"Regulatory task {i} failed: {str(result)}"
                    state["errors"].append(error_msg)
                    logger.error(f"regulatory_task_{i}_failed", error=str(result))
            
            # Create consolidated findings
            all_findings = {
                "fdi": fdi if not isinstance(fdi, Exception) else {},
                "sector_regulations": sector_reg if not isinstance(sector_reg, Exception) else {},
                "tax": tax if not isinstance(tax, Exception) else {},
                "geopolitical": geopolitical if not isinstance(geopolitical, Exception) else {},
                "trade": trade if not isinstance(trade, Exception) else {},
                "labor": labor if not isinstance(labor, Exception) else {}
            }
            
            # Create risk matrix
            logger.info("creating_risk_matrix")
            risk_matrix = await self.create_risk_matrix(
                request["strategic_question"],
                all_findings
            )
            
            # Recommend legal structure
            logger.info("recommending_legal_structure")
            legal_structure = await self.recommend_legal_structure(
                request["company_name"],
                request["strategic_question"],
                all_findings
            )
            
            # Identify blockers
            key_blockers = self._identify_blockers(all_findings)
            
            # Create compliance roadmap
            compliance_roadmap = self._create_compliance_roadmap(all_findings)
            
            # Consolidate all findings
            state["regulatory_findings"] = {
                "fdi_analysis": fdi if not isinstance(fdi, Exception) else {},
                "sector_regulations": sector_reg if not isinstance(sector_reg, Exception) else {},
                "tax_analysis": tax if not isinstance(tax, Exception) else {},
                "geopolitical_assessment": geopolitical if not isinstance(geopolitical, Exception) else {},
                "trade_barriers": trade if not isinstance(trade, Exception) else {},
                "labor_regulations": labor if not isinstance(labor, Exception) else {},
                "risk_matrix": risk_matrix,
                "recommended_structure": legal_structure,
                "overall_risk_level": risk_matrix.get("risk_level", "unknown"),
                "key_blockers": key_blockers,
                "compliance_roadmap": compliance_roadmap,
                "source_country": source_country,
                "target_country": target_country
            }
            
            state["metadata"]["regulatory_time"] = time.time() - start_time
            
            # Log execution
            await self.db.save_agent_log(
                agent_name=self.name,
                execution_time=state["metadata"]["regulatory_time"],
                success=True,
                metadata={
                    "risks_identified": len(risk_matrix.get("risks", [])),
                    "blockers": len(key_blockers)
                }
            )
            
            logger.info(
                "regulatory_agent_complete",
                execution_time=state["metadata"]["regulatory_time"],
                risk_level=risk_matrix.get("risk_level", "unknown"),
                blockers=len(key_blockers)
            )
            
            return state
            
        except Exception as e:
            error_msg = f"Regulatory agent failed: {str(e)}"
            state["errors"].append(error_msg)
            logger.error("regulatory_agent_failed", error=str(e))
            return state
    
    async def assess_fdi_regulations(
        self,
        source_country: str,
        target_country: str,
        industry: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Analyze Foreign Direct Investment regulations.
        
        Args:
            source_country: Source country
            target_country: Target country
            industry: Industry sector
            context: Additional context
            
        Returns:
            FDI analysis dictionary
        """
        try:
            # Fetch FDI policy data
            fdi_policy = await self.regulatory_data.get_fdi_policy(target_country, industry)
            
            prompt = FDI_ANALYSIS_PROMPT.format(
                company=f"{source_country} company",
                source_country=source_country,
                target_country=target_country,
                industry=industry,
                fdi_policy=json.dumps(fdi_policy, indent=2),
                context=context
            )
            
            result = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a regulatory expert analyzing FDI regulations.",
                response_schema={}
            )
            
            return result if isinstance(result, dict) else fdi_policy
            
        except Exception as e:
            logger.error("fdi_assessment_failed", error=str(e))
            return {
                "permitted": True,
                "ownership_cap": 100,
                "approvals_needed": [],
                "conditions": [],
                "timeline_months": 6,
                "key_risks": [str(e)],
                "compliance_complexity": "unknown"
            }
    
    async def evaluate_sector_regulations(
        self,
        industry: str,
        country: str,
        business_model: str
    ) -> Dict[str, Any]:
        """
        Industry-specific regulations analysis.
        
        Args:
            industry: Industry sector
            country: Target country
            business_model: Business model type
            
        Returns:
            Sector regulations dictionary
        """
        try:
            prompt = SECTOR_REGULATIONS_PROMPT.format(
                industry=industry,
                country=country,
                context=f"Business model: {business_model}"
            )
            
            result = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a regulatory compliance expert.",
                response_schema={}
            )
            
            return result if isinstance(result, dict) else {
                "licenses_required": [],
                "regulatory_bodies": [],
                "compliance_cost": "medium",
                "ongoing_obligations": [],
                "penalties_for_violation": []
            }
            
        except Exception as e:
            logger.error("sector_regulations_failed", error=str(e))
            return {
                "licenses_required": [],
                "regulatory_bodies": [],
                "compliance_cost": "unknown",
                "ongoing_obligations": [],
                "penalties_for_violation": []
            }
    
    async def analyze_tax_implications(
        self,
        structure: str,
        countries: List[str]
    ) -> Dict[str, Any]:
        """
        Tax analysis for the structure.
        
        Args:
            structure: Legal structure type
            countries: List of countries involved
            
        Returns:
            Tax analysis dictionary
        """
        try:
            # Fetch tax data for all countries
            tax_data = {}
            for country in countries:
                tax_data[country] = await self.regulatory_data.get_tax_rates(country)
            
            return {
                "countries": tax_data,
                "structure": structure,
                "key_considerations": [
                    "Corporate tax rates vary by country",
                    "Tax treaties may reduce withholding tax",
                    "Transfer pricing rules apply"
                ]
            }
            
        except Exception as e:
            logger.error("tax_analysis_failed", error=str(e))
            return {"countries": {}, "structure": structure, "key_considerations": []}
    
    async def assess_geopolitical_risk(
        self,
        country: str,
        industry: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Political and macroeconomic risk assessment.
        
        Args:
            country: Target country
            industry: Industry sector
            context: Additional context
            
        Returns:
            Geopolitical risk dictionary
        """
        try:
            # Fetch political risk data
            political_data = await self.regulatory_data.get_political_risk_score(country)
            
            prompt = GEOPOLITICAL_RISK_PROMPT.format(
                company=f"Company in {industry}",
                country=country,
                industry=industry,
                political_data=json.dumps(political_data, indent=2),
                economic_data="GDP growth: 3-5%, Inflation: 2-3%",
                news=context[:500]
            )
            
            result = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a geopolitical risk analyst.",
                response_schema={}
            )
            
            if isinstance(result, dict):
                # Merge with political data
                result["political_risk_data"] = political_data
                return result
            
            return political_data
            
        except Exception as e:
            logger.error("geopolitical_risk_failed", error=str(e))
            return {
                "stability_score": 5.0,
                "key_risks": [str(e)],
                "political_trends": [],
                "economic_outlook": "unknown",
                "currency_volatility": "unknown",
                "overall_risk_level": "unknown"
            }
    
    async def evaluate_trade_barriers(
        self,
        export_country: str,
        import_country: str,
        product_category: str
    ) -> Dict[str, Any]:
        """
        Import/export analysis.
        
        Args:
            export_country: Exporting country
            import_country: Importing country
            product_category: Product/service category
            
        Returns:
            Trade barriers dictionary
        """
        try:
            trade_data = await self.regulatory_data.get_trade_data(
                export_country, import_country
            )
            return trade_data
            
        except Exception as e:
            logger.error("trade_barriers_failed", error=str(e))
            return {
                "route": f"{export_country} → {import_country}",
                "tariff_rate": 0.10,
                "free_trade_agreement": False,
                "quotas": [],
                "restrictions": []
            }
    
    async def assess_labor_regulations(
        self,
        country: str,
        industry: str
    ) -> Dict[str, Any]:
        """
        Employment law considerations.
        
        Args:
            country: Target country
            industry: Industry sector
            
        Returns:
            Labor regulations dictionary
        """
        try:
            labor_data = await self.regulatory_data.get_labor_laws(country)
            return labor_data
            
        except Exception as e:
            logger.error("labor_regulations_failed", error=str(e))
            return {
                "min_wage_usd_monthly": 500,
                "standard_hours_per_week": 40,
                "mandatory_benefits": [],
                "local_hiring_requirement": 0.0,
                "union_presence": "unknown"
            }
    
    async def create_risk_matrix(
        self,
        strategy: str,
        all_findings: Dict
    ) -> Dict[str, Any]:
        """
        Consolidate all risks into matrix.
        
        Args:
            strategy: Strategic question
            all_findings: All regulatory findings
            
        Returns:
            Risk matrix dictionary
        """
        try:
            prompt = REGULATORY_RISK_MATRIX_PROMPT.format(
                strategy=strategy,
                fdi=json.dumps(all_findings.get("fdi", {}), indent=2)[:500],
                tax=json.dumps(all_findings.get("tax", {}), indent=2)[:500],
                trade=json.dumps(all_findings.get("trade", {}), indent=2)[:500],
                labor=json.dumps(all_findings.get("labor", {}), indent=2)[:500],
                geopolitical=json.dumps(all_findings.get("geopolitical", {}), indent=2)[:500]
            )
            
            result = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a risk management consultant.",
                response_schema={}
            )
            
            return result if isinstance(result, dict) else {
                "risks": [],
                "total_risk_score": 0,
                "risk_level": "unknown",
                "critical_risks": []
            }
            
        except Exception as e:
            logger.error("risk_matrix_failed", error=str(e))
            return {
                "risks": [],
                "total_risk_score": 0,
                "risk_level": "unknown",
                "critical_risks": []
            }
    
    async def recommend_legal_structure(
        self,
        company: str,
        strategy: str,
        analysis: Dict
    ) -> Dict[str, Any]:
        """
        Recommend optimal legal structure.
        
        Args:
            company: Company name
            strategy: Strategic question
            analysis: Regulatory analysis
            
        Returns:
            Legal structure recommendation
        """
        try:
            prompt = LEGAL_STRUCTURE_PROMPT.format(
                company=company,
                strategy=strategy,
                regulatory_summary=json.dumps(analysis, indent=2)[:1000],
                business_requirements="Full operational control, tax efficiency"
            )
            
            result = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a corporate structuring advisor.",
                response_schema={}
            )
            
            return result if isinstance(result, dict) else {
                "recommended_structure": "Wholly-owned subsidiary",
                "rationale": "Full control and liability protection",
                "pros": [],
                "cons": [],
                "alternatives": [],
                "setup_timeline": "6-9 months",
                "estimated_cost": "$50K-$100K"
            }
            
        except Exception as e:
            logger.error("legal_structure_failed", error=str(e))
            return {
                "recommended_structure": "Unknown",
                "rationale": str(e),
                "pros": [],
                "cons": [],
                "alternatives": [],
                "setup_timeline": "Unknown",
                "estimated_cost": "Unknown"
            }
    
    def _extract_source_country(self, request: Dict) -> str:
        """Extract source country from request."""
        # Simple heuristic: check company name
        company = request.get("company_name", "").lower()
        
        if any(name in company for name in ["zomato", "swiggy", "ola", "flipkart", "paytm", "tata"]):
            return "India"
        elif "uber" in company or "amazon" in company:
            return "USA"
        else:
            return "India"  # Default
    
    def _extract_target_country(self, question: str) -> str:
        """Extract target country from strategic question."""
        question_lower = question.lower()
        
        countries = {
            "saudi arabia": "Saudi Arabia",
            "saudi": "Saudi Arabia",
            "uae": "UAE",
            "dubai": "UAE",
            "singapore": "Singapore",
            "usa": "USA",
            "united states": "USA",
            "uk": "UK",
            "united kingdom": "UK",
            "india": "India"
        }
        
        for keyword, country in countries.items():
            if keyword in question_lower:
                return country
        
        return "Saudi Arabia"  # Default
    
    def _identify_blockers(self, findings: Dict) -> List[str]:
        """Identify regulatory blockers."""
        blockers = []
        
        fdi = findings.get("fdi", {})
        if not fdi.get("permitted", True):
            blockers.append("FDI not permitted in this sector")
        
        if fdi.get("ownership_cap", 100) < 51:
            blockers.append(f"Ownership limited to {fdi.get('ownership_cap')}% - majority control not possible")
        
        geopolitical = findings.get("geopolitical", {})
        if geopolitical.get("overall_risk_level") == "critical":
            blockers.append("Critical geopolitical risk level")
        
        return blockers
    
    def _create_compliance_roadmap(self, findings: Dict) -> List[Dict]:
        """Create step-by-step compliance roadmap."""
        roadmap = [
            {
                "phase": "Pre-Entry (Months 1-3)",
                "tasks": [
                    "Conduct regulatory due diligence",
                    "Obtain FDI approval (if required)",
                    "Register legal entity",
                    "Apply for sector-specific licenses"
                ],
                "estimated_duration": "3 months"
            },
            {
                "phase": "Setup (Months 4-6)",
                "tasks": [
                    "Establish bank accounts",
                    "Register for tax and VAT",
                    "Hire local team (comply with local hiring quotas)",
                    "Setup compliance systems"
                ],
                "estimated_duration": "3 months"
            },
            {
                "phase": "Operations (Month 7+)",
                "tasks": [
                    "Ongoing compliance reporting",
                    "Annual audits and tax filings",
                    "Regulatory relationship management",
                    "Monitor policy changes"
                ],
                "estimated_duration": "Ongoing"
            }
        ]
        
        return roadmap
