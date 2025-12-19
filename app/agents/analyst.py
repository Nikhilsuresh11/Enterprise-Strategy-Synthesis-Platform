"""Analyst Agent - Financial and market analysis."""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.llm_service import LLMService
from app.services.db_service import DatabaseService
from app.services.chart_service import ChartService
from app.services import financial_calcs as fc
from app.models.state import AgentState
from app.agents.prompts.analyst_prompts import (
    TAM_SAM_SOM_PROMPT,
    COMPETITIVE_ANALYSIS_PROMPT,
    PORTERS_FIVE_FORCES_PROMPT,
    SCENARIO_MODELING_PROMPT,
    UNIT_ECONOMICS_PROMPT
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AnalystAgent:
    """
    Analyst Agent performs financial and market analysis:
    - Market sizing (TAM/SAM/SOM)
    - Unit economics (CAC, LTV)
    - Revenue modeling
    - Scenario analysis
    - DCF valuation
    - Competitive benchmarking
    - Porter's Five Forces
    """
    
    def __init__(self, llm: LLMService, db: DatabaseService):
        """
        Initialize Analyst Agent.
        
        Args:
            llm: LLM service for analysis
            db: Database service for logging
        """
        self.llm = llm
        self.db = db
        self.name = "analyst_agent"
        self.chart_service = ChartService()
        
        logger.info("analyst_agent_initialized")
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Main execution: performs all financial and market analysis.
        
        Args:
            state: Current agent state with research_data
            
        Returns:
            Updated state with market_analysis and financial_model
        """
        try:
            request = state["request"]
            research_data = state.get("research_data", {})
            
            logger.info(
                "analyst_agent_starting",
                company=request["company_name"],
                industry=request["industry"]
            )
            
            start_time = time.time()
            
            # 1. Market Sizing
            logger.info("calculating_market_sizing")
            market_size = await self.calculate_tam_sam_som(
                company=request["company_name"],
                industry=request["industry"],
                region="global",
                market_data=research_data.get("market_context", {}),
                research_context=json.dumps(research_data, indent=2)[:2000]
            )
            
            # 2. Unit Economics
            logger.info("analyzing_unit_economics")
            unit_econ = await self.analyze_unit_economics(
                company=request["company_name"],
                business_model="B2C",  # Could be inferred from context
                financial_data=research_data.get("financial_snapshot", {})
            )
            
            # 3. Revenue Model
            logger.info("building_revenue_model")
            revenue_model = await self.build_revenue_model(
                base_data=research_data.get("financial_snapshot", {}),
                market_size=market_size,
                assumptions={},
                years=5
            )
            
            # 4. Scenario Analysis
            logger.info("creating_scenarios")
            scenarios = await self.scenario_analysis(
                company=request["company_name"],
                strategy=request.get("strategic_question", ""),
                base_model=revenue_model,
                risk_factors=[]
            )
            
            # 5. Valuation (if we have projections)
            valuation = {}
            if "base" in scenarios and scenarios["base"]:
                logger.info("calculating_valuation")
                valuation = await self.dcf_valuation(
                    projections=scenarios["base"],
                    wacc=0.10,
                    terminal_growth=0.03
                )
            
            # 6. Competitive Analysis
            logger.info("competitive_benchmarking")
            competitive = await self.competitive_benchmarking(
                company=request["company_name"],
                industry=request["industry"],
                company_data=research_data.get("financial_snapshot", {}),
                competitor_data=research_data.get("competitive_overview", {})
            )
            
            # 7. Porter's Five Forces
            logger.info("porters_analysis")
            porters = await self.porters_five_forces(
                industry=request["industry"],
                market_context=json.dumps(research_data.get("market_context", {})),
                competitive_data=research_data.get("competitive_overview", {})
            )
            
            # 8. Update state
            state["market_analysis"] = market_size
            state["financial_model"] = {
                "unit_economics": unit_econ,
                "revenue_projections": revenue_model,
                "scenarios": scenarios,
                "valuation": valuation,
                "competitive_position": competitive,
                "porters_analysis": porters
            }
            
            # 9. Generate Charts
            logger.info("generating_charts")
            charts = {}
            
            try:
                # Market sizing funnel
                if all(k in market_size for k in ["TAM", "SAM", "SOM"]):
                    charts["market_sizing"] = self.chart_service.create_market_sizing_chart(
                        tam=market_size["TAM"].get("value_usd_millions", 0),
                        sam=market_size["SAM"].get("value_usd_millions", 0),
                        som=market_size["SOM"].get("year_5_usd_millions", 0)
                    )
                
                # Revenue scenarios
                if scenarios:
                    charts["scenarios"] = self.chart_service.create_revenue_projection_chart(
                        scenarios=scenarios
                    )
                
                # Porter's Five Forces
                if "forces" in porters:
                    charts["porters"] = self.chart_service.create_porters_five_forces_chart(
                        forces=porters["forces"]
                    )
                
                # Unit economics
                if "CAC" in unit_econ and "LTV" in unit_econ:
                    charts["unit_economics"] = self.chart_service.create_unit_economics_chart(
                        cac=unit_econ["CAC"],
                        ltv=unit_econ["LTV"]
                    )
                
            except Exception as e:
                logger.error("chart_generation_failed", error=str(e))
            
            state["metadata"]["charts"] = charts
            state["metadata"]["analyst_time"] = time.time() - start_time
            
            # 10. Log execution
            await self.db.save_agent_log(
                agent_name=self.name,
                execution_time=state["metadata"]["analyst_time"],
                success=True,
                metadata={
                    "analysis_complete": True,
                    "charts_generated": len(charts)
                }
            )
            
            logger.info(
                "analyst_agent_complete",
                execution_time=state["metadata"]["analyst_time"],
                charts=len(charts)
            )
            
            # Update progress: Analyst complete (50%)
            if "db_service" in state["metadata"] and "job_id" in state["metadata"]:
                try:
                    await state["metadata"]["db_service"].update_session_status(
                        state["metadata"]["job_id"], "processing", 50
                    )
                except Exception as e:
                    logger.warning("progress_update_failed", error=str(e))
            
            return state
            
        except Exception as e:
            error_msg = f"Analyst agent failed: {str(e)}"
            # Defensive: ensure errors list exists
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(error_msg)
            logger.error("analyst_agent_failed", error=str(e), exc_info=True)
            return state
    
    async def calculate_tam_sam_som(
        self,
        company: str,
        industry: str,
        region: str,
        market_data: Dict,
        research_context: str
    ) -> Dict[str, Any]:
        """
        Calculate market sizing using LLM + formulas.
        
        Args:
            company: Company name
            industry: Industry name
            region: Geographic region
            market_data: Market context from research
            research_context: Full research data as string
            
        Returns:
            TAM/SAM/SOM dictionary
        """
        try:
            prompt = TAM_SAM_SOM_PROMPT.format(
                company=company,
                industry=industry,
                region=region,
                market_data=json.dumps(market_data, indent=2),
                research_context=research_context
            )
            
            result = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a senior financial analyst at McKinsey & Company.",
                response_schema={}
            )
            
            # Validate and apply formulas if needed
            if isinstance(result, dict):
                # Calculate SOM progression using S-curve
                if "SOM" in result:
                    som_data = result["SOM"]
                    if "year_5_usd_millions" in som_data and "SAM" in result:
                        sam_value = result["SAM"].get("value_usd_millions", 0)
                        year_5_som = som_data.get("year_5_usd_millions", 0)
                        
                        if sam_value > 0:
                            market_share = year_5_som / sam_value
                            progression = fc.calculate_som(sam_value, market_share, 5)
                            result["SOM"]["yearly_progression"] = progression["yearly_progression"]
                
                return result
            
            # Fallback structure
            return {
                "TAM": {"value_usd_millions": 0, "methodology": "unknown", "assumptions": []},
                "SAM": {"value_usd_millions": 0, "assumptions": []},
                "SOM": {"year_1_usd_millions": 0, "year_5_usd_millions": 0, "assumptions": []}
            }
            
        except Exception as e:
            logger.error("tam_sam_som_failed", error=str(e))
            return {
                "TAM": {"value_usd_millions": 0, "methodology": "error", "assumptions": []},
                "SAM": {"value_usd_millions": 0, "assumptions": []},
                "SOM": {"year_1_usd_millions": 0, "year_5_usd_millions": 0, "assumptions": []}
            }
    
    async def analyze_unit_economics(
        self,
        company: str,
        business_model: str,
        financial_data: Dict
    ) -> Dict[str, Any]:
        """
        Calculate unit economics metrics.
        
        Args:
            company: Company name
            business_model: Business model type
            financial_data: Financial data from research
            
        Returns:
            Unit economics dictionary
        """
        try:
            prompt = UNIT_ECONOMICS_PROMPT.format(
                company=company,
                business_model=business_model,
                financial_data=json.dumps(financial_data, indent=2)
            )
            
            result = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a financial analyst calculating unit economics.",
                response_schema={}
            )
            
            if isinstance(result, dict):
                # Calculate payback period if we have CAC and LTV
                if "CAC" in result and "LTV" in result:
                    cac = result["CAC"]
                    ltv = result["LTV"]
                    
                    # Estimate monthly revenue (LTV / 24 months average)
                    monthly_revenue = ltv / 24
                    gross_margin = result.get("contribution_margin_pct", 0.6)
                    
                    payback = fc.calculate_payback_period(cac, monthly_revenue, gross_margin)
                    result["payback_months"] = min(payback, 999)  # Cap at 999
                
                return result
            
            return {"CAC": 0, "LTV": 0, "LTV_CAC_ratio": 0, "assessment": "unknown"}
            
        except Exception as e:
            logger.error("unit_economics_failed", error=str(e))
            return {"CAC": 0, "LTV": 0, "LTV_CAC_ratio": 0, "assessment": "error"}
    
    async def build_revenue_model(
        self,
        base_data: Dict,
        market_size: Dict,
        assumptions: Dict,
        years: int = 5
    ) -> Dict[str, Any]:
        """
        Build 5-year revenue projection.
        
        Args:
            base_data: Base financial data
            market_size: TAM/SAM/SOM data
            assumptions: Additional assumptions
            years: Number of years to project
            
        Returns:
            Revenue model dictionary
        """
        try:
            # Extract SOM progression if available
            som_data = market_size.get("SOM", {})
            
            if "yearly_progression" in som_data:
                projections = som_data["yearly_progression"]
            else:
                # Simple linear growth model
                year_1 = som_data.get("year_1_usd_millions", 10)
                year_5 = som_data.get("year_5_usd_millions", 100)
                
                growth_rate = ((year_5 / year_1) ** (1/4)) - 1 if year_1 > 0 else 0.5
                
                projections = []
                for year in range(years):
                    value = year_1 * ((1 + growth_rate) ** year)
                    projections.append(value)
            
            return {
                "projections": projections[:years],
                "growth_rates": [
                    ((projections[i+1] / projections[i]) - 1) if projections[i] > 0 else 0
                    for i in range(len(projections)-1)
                ],
                "assumptions": assumptions
            }
            
        except Exception as e:
            logger.error("revenue_model_failed", error=str(e))
            return {"projections": [0] * years, "growth_rates": [], "assumptions": {}}
    
    async def scenario_analysis(
        self,
        company: str,
        strategy: str,
        base_model: Dict,
        risk_factors: List[Dict]
    ) -> Dict[str, List[float]]:
        """
        Create 3 scenarios: Base, Upside, Downside.
        
        Args:
            company: Company name
            strategy: Strategic question
            base_model: Base revenue model
            risk_factors: List of risk factors
            
        Returns:
            Dictionary with base, upside, downside scenarios
        """
        try:
            prompt = SCENARIO_MODELING_PROMPT.format(
                company=company,
                strategy=strategy,
                base_projections=json.dumps(base_model, indent=2),
                risks=json.dumps(risk_factors, indent=2)
            )
            
            result = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a financial modeler creating scenario analysis.",
                response_schema={}
            )
            
            if isinstance(result, dict):
                return {
                    "base": result.get("base", {}).get("revenue_projections", []),
                    "upside": result.get("upside", {}).get("revenue_projections", []),
                    "downside": result.get("downside", {}).get("revenue_projections", [])
                }
            
            # Fallback: create scenarios from base model
            base_proj = base_model.get("projections", [10, 25, 50, 80, 100])
            
            return {
                "base": base_proj,
                "upside": [v * 1.5 for v in base_proj],
                "downside": [v * 0.6 for v in base_proj]
            }
            
        except Exception as e:
            logger.error("scenario_analysis_failed", error=str(e))
            base_proj = base_model.get("projections", [10, 25, 50, 80, 100])
            return {
                "base": base_proj,
                "upside": [v * 1.5 for v in base_proj],
                "downside": [v * 0.6 for v in base_proj]
            }
    
    async def dcf_valuation(
        self,
        projections: List[float],
        wacc: float,
        terminal_growth: float
    ) -> Dict[str, Any]:
        """
        DCF valuation calculation.
        
        Args:
            projections: Revenue projections
            wacc: Weighted average cost of capital
            terminal_growth: Terminal growth rate
            
        Returns:
            Valuation dictionary
        """
        try:
            # Assume 20% FCF margin
            fcf_projections = [p * 0.20 for p in projections]
            
            valuation = fc.dcf_valuation(fcf_projections, wacc, terminal_growth)
            
            logger.info("dcf_calculated", enterprise_value=valuation["enterprise_value"])
            return valuation
            
        except Exception as e:
            logger.error("dcf_valuation_failed", error=str(e))
            return {"enterprise_value": 0, "assumptions": {}}
    
    async def competitive_benchmarking(
        self,
        company: str,
        industry: str,
        company_data: Dict,
        competitor_data: Dict
    ) -> Dict[str, Any]:
        """
        Benchmark against competitors.
        
        Args:
            company: Company name
            industry: Industry name
            company_data: Company financial data
            competitor_data: Competitor information
            
        Returns:
            Competitive analysis dictionary
        """
        try:
            prompt = COMPETITIVE_ANALYSIS_PROMPT.format(
                company=company,
                industry=industry,
                company_data=json.dumps(company_data, indent=2),
                competitor_data=json.dumps(competitor_data, indent=2)
            )
            
            result = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a competitive intelligence analyst.",
                response_schema={}
            )
            
            return result if isinstance(result, dict) else {
                "positioning": "unknown",
                "market_share_estimate": 0,
                "key_differentiators": [],
                "competitive_gaps": []
            }
            
        except Exception as e:
            logger.error("competitive_benchmarking_failed", error=str(e))
            return {
                "positioning": "unknown",
                "market_share_estimate": 0,
                "key_differentiators": [],
                "competitive_gaps": []
            }
    
    async def porters_five_forces(
        self,
        industry: str,
        market_context: str,
        competitive_data: Dict
    ) -> Dict[str, Any]:
        """
        Porter's Five Forces analysis.
        
        Args:
            industry: Industry name
            market_context: Market context string
            competitive_data: Competitive information
            
        Returns:
            Porter's analysis dictionary
        """
        try:
            prompt = PORTERS_FIVE_FORCES_PROMPT.format(
                industry=industry,
                context=market_context,
                competitive_data=json.dumps(competitive_data, indent=2)
            )
            
            result = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a strategy consultant conducting Porter's Five Forces analysis.",
                response_schema={}
            )
            
            return result if isinstance(result, dict) else {
                "forces": {},
                "overall_attractiveness": "unknown",
                "key_insights": []
            }
            
        except Exception as e:
            logger.error("porters_analysis_failed", error=str(e))
            return {
                "forces": {},
                "overall_attractiveness": "unknown",
                "key_insights": []
            }
