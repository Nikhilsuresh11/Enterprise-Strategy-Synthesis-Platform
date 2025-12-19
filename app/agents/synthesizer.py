"""Synthesizer Agent - Final recommendations and slide generation."""

import time
import json
from typing import Dict, Any, List, Optional

from app.services.llm_service import LLMService
from app.services.db_service import DatabaseService
from app.services.slide_builder import SlideBuilder
from app.models.state import AgentState
from app.agents.prompts.synthesis_prompts import (
    EXECUTIVE_SUMMARY_PROMPT,
    RECOMMENDATION_SYNTHESIS_PROMPT,
    IMPLEMENTATION_ROADMAP_PROMPT,
    ALTERNATIVES_PROMPT
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SynthesizerAgent:
    """
    Synthesizer Agent creates final recommendations and slide decks:
    - Executive summary with clear recommendation
    - Implementation roadmap
    - Success metrics
    - Complete slide deck (12-15 slides)
    - Alternative scenarios (if declined)
    """
    
    def __init__(self, llm: LLMService, db: DatabaseService):
        """
        Initialize Synthesizer Agent.
        
        Args:
            llm: LLM service for synthesis
            db: Database service for logging
        """
        self.llm = llm
        self.db = db
        self.name = "synthesizer_agent"
        
        logger.info("synthesizer_agent_initialized")
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Main execution: synthesize all analysis into final output.
        
        Args:
            state: Current agent state with all analysis complete
            
        Returns:
            Updated state with synthesis and slides
        """
        try:
            logger.info("synthesizer_agent_starting")
            
            start_time = time.time()
            
            request = state["request"]
            research = state.get("research_data", {})
            market_analysis = state.get("market_analysis", {})
            financial_model = state.get("financial_model", {})
            regulatory = state.get("regulatory_findings", {})
            
            # 1. Generate Executive Summary
            logger.info("generating_executive_summary")
            exec_summary = await self.generate_executive_summary(
                request, research, market_analysis, financial_model, regulatory
            )
            
            # 2. Synthesize narratives
            logger.info("synthesizing_narratives")
            market_narrative = await self.synthesize_market_opportunity(market_analysis)
            financial_narrative = await self.synthesize_financial_case(financial_model)
            risk_assessment = await self.synthesize_risk_assessment(regulatory, market_analysis)
            
            # 3. Create Implementation Roadmap
            logger.info("creating_implementation_roadmap")
            implementation = await self.create_implementation_roadmap(
                exec_summary, regulatory, financial_model
            )
            
            # 4. Identify Success Metrics
            logger.info("identifying_success_metrics")
            metrics = await self.identify_success_metrics(
                exec_summary, financial_model
            )
            
            # 5. Generate Alternatives (if declined)
            alternatives = []
            if exec_summary.get("recommendation") == "decline":
                logger.info("generating_alternatives")
                alternatives = await self.generate_alternative_scenarios(state)
            
            # 6. Build Complete Slide Deck
            logger.info("building_slide_deck")
            slides = SlideBuilder.build_complete_deck(
                request,
                exec_summary,
                market_analysis,
                financial_model,
                regulatory,
                state.get("metadata", {}).get("charts", {}),
                implementation
            )
            
            # 7. Update State
            state["synthesis"] = {
                "executive_summary": exec_summary,
                "market_opportunity_narrative": market_narrative,
                "financial_case_narrative": financial_narrative,
                "risk_assessment": risk_assessment,
                "implementation_roadmap": implementation,
                "success_metrics": metrics,
                "alternatives": alternatives
            }
            
            state["slides"] = slides
            state["metadata"]["synthesis_time"] = time.time() - start_time
            
            # Log execution
            await self.db.save_agent_log(
                agent_name=self.name,
                execution_time=state["metadata"]["synthesis_time"],
                success=True,
                metadata={
                    "slides_generated": len(slides),
                    "recommendation": exec_summary.get("recommendation", "unknown")
                }
            )
            
            logger.info(
                "synthesizer_agent_complete",
                execution_time=state["metadata"]["synthesis_time"],
                slides=len(slides),
                recommendation=exec_summary.get("recommendation", "unknown")
            )
            
            # Update progress: Synthesizer complete (90%)
            if "db_service" in state["metadata"] and "job_id" in state["metadata"]:
                try:
                    await state["metadata"]["db_service"].update_session_status(
                        state["metadata"]["job_id"], "processing", 90
                    )
                except Exception as e:
                    logger.warning("progress_update_failed", error=str(e))
            
            return state
            
        except Exception as e:
            error_msg = f"Synthesizer agent failed: {str(e)}"
            # Defensive: ensure errors list exists
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(error_msg)
            logger.error("synthesizer_agent_failed", error=str(e), exc_info=True)
            return state
    
    async def generate_executive_summary(
        self,
        request: Dict,
        research: Dict,
        market_analysis: Dict,
        financial_model: Dict,
        regulatory: Dict
    ) -> Dict[str, Any]:
        """
        Create executive summary with final recommendation.
        
        Returns:
            Executive summary dictionary
        """
        try:
            # Extract key data
            tam = market_analysis.get('TAM', {}).get('value_usd_millions', 0)
            sam = market_analysis.get('SAM', {}).get('value_usd_millions', 0)
            som = market_analysis.get('SOM', {}).get('year_5_usd_millions', 0)
            
            scenarios = financial_model.get('scenarios', {})
            revenue_y5 = scenarios.get('base', [0])[-1] if scenarios.get('base') else 0
            
            unit_econ = financial_model.get('unit_economics', {})
            ltv_cac = unit_econ.get('LTV_CAC_ratio', 0)
            
            valuation = financial_model.get('valuation', {}).get('enterprise_value', 0)
            
            comp_pos = financial_model.get('competitive_position', {})
            
            # Build prompt
            prompt = EXECUTIVE_SUMMARY_PROMPT.format(
                question=request.get('strategic_question', ''),
                research_summary=json.dumps(research.get('key_findings', [])[:3])[:500],
                tam=tam,
                sam=sam,
                som=som,
                competitive_summary=comp_pos.get('positioning', 'Unknown'),
                revenue_y5=revenue_y5,
                ltv_cac_ratio=ltv_cac,
                unit_econ_assessment=unit_econ.get('assessment', 'unknown'),
                valuation=valuation,
                regulatory_risk=regulatory.get('overall_risk_level', 'unknown'),
                blockers=', '.join(regulatory.get('key_blockers', [])[:2]) or 'None',
                legal_structure=regulatory.get('recommended_structure', {}).get('recommended_structure', 'Unknown')
            )
            
            result = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a McKinsey Partner creating an executive summary.",
                response_schema={}
            )
            
            return result if isinstance(result, dict) else {
                "recommendation": "conditional",
                "confidence": 0.7,
                "supporting_points": ["Market opportunity exists", "Financial model viable", "Risks manageable"],
                "key_risks": ["Execution risk", "Market competition", "Regulatory complexity"],
                "expected_impact": "Significant market presence",
                "timeline": "5 years",
                "conditions": []
            }
            
        except Exception as e:
            logger.error("executive_summary_failed", error=str(e))
            return {
                "recommendation": "conditional",
                "confidence": 0.5,
                "supporting_points": ["Analysis complete"],
                "key_risks": ["Further analysis needed"],
                "expected_impact": "Unknown",
                "timeline": "Unknown",
                "conditions": []
            }
    
    async def synthesize_market_opportunity(
        self,
        market_analysis: Dict
    ) -> str:
        """
        Create narrative summary of market opportunity.
        
        Returns:
            3-4 sentence narrative
        """
        try:
            tam = market_analysis.get('TAM', {}).get('value_usd_millions', 0)
            sam = market_analysis.get('SAM', {}).get('value_usd_millions', 0)
            som = market_analysis.get('SOM', {}).get('year_5_usd_millions', 0)
            
            narrative = f"The market opportunity represents a Total Addressable Market of ${tam:,.0f}M, "
            narrative += f"with a Serviceable Addressable Market of ${sam:,.0f}M. "
            narrative += f"Based on competitive dynamics and realistic penetration assumptions, "
            narrative += f"the Serviceable Obtainable Market is estimated at ${som:,.0f}M by Year 5. "
            narrative += "This represents a significant and achievable market opportunity."
            
            return narrative
            
        except Exception as e:
            logger.error("market_narrative_failed", error=str(e))
            return "Market opportunity analysis completed."
    
    async def synthesize_financial_case(
        self,
        financial_model: Dict
    ) -> str:
        """
        Create financial case summary.
        
        Returns:
            Financial narrative
        """
        try:
            unit_econ = financial_model.get('unit_economics', {})
            ltv_cac = unit_econ.get('LTV_CAC_ratio', 0)
            
            valuation = financial_model.get('valuation', {}).get('enterprise_value', 0)
            
            scenarios = financial_model.get('scenarios', {})
            base_y5 = scenarios.get('base', [0])[-1] if scenarios.get('base') else 0
            
            narrative = f"The financial model demonstrates strong unit economics with an LTV/CAC ratio of {ltv_cac:.1f}x, "
            narrative += "well above the 3:1 benchmark for sustainable growth. "
            narrative += f"Base case projections show revenue reaching ${base_y5:,.0f}M by Year 5. "
            narrative += f"DCF valuation yields an enterprise value of ${valuation:,.0f}M, "
            narrative += "indicating attractive returns for investors."
            
            return narrative
            
        except Exception as e:
            logger.error("financial_narrative_failed", error=str(e))
            return "Financial analysis completed."
    
    async def synthesize_risk_assessment(
        self,
        regulatory: Dict,
        market_analysis: Dict
    ) -> Dict[str, Any]:
        """
        Consolidated risk assessment.
        
        Returns:
            Risk assessment dictionary
        """
        try:
            risk_matrix = regulatory.get('risk_matrix', {})
            risks = risk_matrix.get('risks', [])
            
            # Get top 5 risks
            top_risks = sorted(risks, key=lambda x: x.get('score', 0), reverse=True)[:5]
            
            # Format for output
            formatted_risks = []
            for risk in top_risks:
                formatted_risks.append({
                    "risk": risk.get('risk', 'Unknown'),
                    "probability": f"{risk.get('probability', 3)}/5",
                    "impact": f"{risk.get('impact', 3)}/5",
                    "mitigation": risk.get('mitigation', 'Under review')
                })
            
            overall_risk = regulatory.get('overall_risk_level', 'medium')
            
            # Determine risk appetite
            if overall_risk == 'low':
                risk_appetite = 'acceptable'
            elif overall_risk in ['medium', 'high']:
                risk_appetite = 'marginal'
            else:
                risk_appetite = 'unacceptable'
            
            return {
                "top_risks": formatted_risks,
                "overall_risk": overall_risk,
                "risk_appetite": risk_appetite
            }
            
        except Exception as e:
            logger.error("risk_assessment_failed", error=str(e))
            return {
                "top_risks": [],
                "overall_risk": "unknown",
                "risk_appetite": "unknown"
            }
    
    async def create_implementation_roadmap(
        self,
        recommendation: Dict,
        regulatory: Dict,
        financial_model: Dict
    ) -> List[Dict[str, Any]]:
        """
        Create 6-12 month implementation plan.
        
        Returns:
            List of phase dictionaries
        """
        try:
            prompt = IMPLEMENTATION_ROADMAP_PROMPT.format(
                strategy=recommendation.get('recommendation', 'proceed'),
                recommendation=recommendation.get('recommendation', 'proceed'),
                timeline=recommendation.get('timeline', '12 months'),
                requirements=json.dumps(regulatory.get('compliance_roadmap', []))[:500]
            )
            
            result = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a strategy consultant creating an implementation roadmap.",
                response_schema={}
            )
            
            if isinstance(result, dict) and 'phases' in result:
                return result['phases']
            
            # Fallback roadmap
            return regulatory.get('compliance_roadmap', [
                {
                    "phase": "Preparation (Months 1-3)",
                    "duration": "3 months",
                    "milestones": ["Regulatory approval", "Entity setup"],
                    "key_activities": ["File applications", "Hire team"],
                    "resources_required": ["Legal counsel", "Initial capital"],
                    "success_metrics": ["Approvals obtained", "Team in place"],
                    "risks": ["Approval delays"]
                }
            ])
            
        except Exception as e:
            logger.error("implementation_roadmap_failed", error=str(e))
            return []
    
    async def identify_success_metrics(
        self,
        recommendation: Dict,
        financial_model: Dict
    ) -> List[Dict[str, Any]]:
        """
        Define KPIs to track success.
        
        Returns:
            List of metric dictionaries
        """
        try:
            metrics = [
                {
                    "metric": "Market Share",
                    "type": "lagging",
                    "target": "10% by Year 5",
                    "frequency": "quarterly"
                },
                {
                    "metric": "Customer Acquisition Cost (CAC)",
                    "type": "leading",
                    "target": f"${financial_model.get('unit_economics', {}).get('CAC', 200):.0f}",
                    "frequency": "monthly"
                },
                {
                    "metric": "LTV/CAC Ratio",
                    "type": "leading",
                    "target": ">3.0x",
                    "frequency": "monthly"
                },
                {
                    "metric": "Revenue Growth",
                    "type": "lagging",
                    "target": "50% YoY",
                    "frequency": "quarterly"
                },
                {
                    "metric": "Customer Retention Rate",
                    "type": "leading",
                    "target": ">85%",
                    "frequency": "monthly"
                }
            ]
            
            return metrics
            
        except Exception as e:
            logger.error("success_metrics_failed", error=str(e))
            return []
    
    async def generate_alternative_scenarios(
        self,
        state: AgentState
    ) -> List[Dict[str, Any]]:
        """
        Generate alternative strategies if recommendation is decline.
        
        Returns:
            List of alternative strategies
        """
        try:
            request = state["request"]
            
            prompt = ALTERNATIVES_PROMPT.format(
                declined_strategy=request.get('strategic_question', ''),
                decline_reason="Risk/reward profile unfavorable"
            )
            
            result = await self.llm.generate_structured_output(
                prompt=prompt,
                system_prompt="You are a strategy consultant proposing alternatives.",
                response_schema={}
            )
            
            if isinstance(result, dict) and 'alternatives' in result:
                return result['alternatives']
            
            return []
            
        except Exception as e:
            logger.error("alternatives_failed", error=str(e))
            return []
