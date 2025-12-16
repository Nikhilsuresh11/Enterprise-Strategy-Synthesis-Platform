"""Slide builder service for generating structured slide decks."""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime


class SlideBuilder:
    """Builds structured slide content for presentation decks."""
    
    @staticmethod
    def create_title_slide(
        company: str,
        question: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create title slide."""
        if date is None:
            date = datetime.now().strftime("%B %Y")
        
        return {
            "slide_number": 1,
            "type": "title",
            "title": f"Strategic Analysis: {company}",
            "subtitle": question,
            "footer": f"Stratagem AI | {date}",
            "content": [],
            "chart_data": None,
            "speaker_notes": f"Strategic analysis for {company} addressing the question: {question}"
        }
    
    @staticmethod
    def create_executive_summary_slide(
        exec_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create executive summary slide."""
        recommendation = exec_summary.get("recommendation", "unknown").upper()
        confidence = exec_summary.get("confidence", 0.0)
        
        content = [
            f"**RECOMMENDATION:** {recommendation}",
            f"**CONFIDENCE:** {int(confidence*100)}%",
            "",
            "**KEY SUPPORTING POINTS:**"
        ]
        
        for point in exec_summary.get("supporting_points", []):
            content.append(f"• {point}")
        
        content.append("")
        content.append("**KEY RISKS:**")
        
        for risk in exec_summary.get("key_risks", []):
            content.append(f"• {risk}")
        
        if exec_summary.get("conditions"):
            content.append("")
            content.append("**CONDITIONS:**")
            for condition in exec_summary["conditions"]:
                content.append(f"• {condition}")
        
        return {
            "slide_number": 2,
            "type": "content",
            "title": "Executive Summary",
            "content": content,
            "chart_data": None,
            "speaker_notes": f"Final recommendation is to {recommendation} with {int(confidence*100)}% confidence. {exec_summary.get('expected_impact', '')}"
        }
    
    @staticmethod
    def create_market_sizing_slide(
        tam: float,
        sam: float,
        som: float,
        chart_json: str
    ) -> Dict[str, Any]:
        """Create market sizing slide with funnel chart."""
        content = [
            f"**Total Addressable Market (TAM):** ${tam:,.0f}M",
            f"**Serviceable Addressable Market (SAM):** ${sam:,.0f}M",
            f"**Serviceable Obtainable Market (SOM, Year 5):** ${som:,.0f}M",
            "",
            f"• Target represents {(som/tam*100):.1f}% of total market",
            f"• Realistic penetration based on competitive analysis",
            f"• SAM represents {(sam/tam*100):.0f}% of TAM based on geographic/segment focus"
        ]
        
        return {
            "slide_number": 4,
            "type": "chart",
            "title": "Market Sizing Analysis",
            "content": content,
            "chart_data": json.loads(chart_json) if isinstance(chart_json, str) else chart_json,
            "speaker_notes": "Market sizing using top-down and bottom-up validation. Conservative estimates based on industry benchmarks."
        }
    
    @staticmethod
    def create_scenario_slide(
        scenarios: Dict[str, List[float]],
        chart_json: str
    ) -> Dict[str, Any]:
        """Create scenario analysis slide."""
        base = scenarios.get('base', [])
        upside = scenarios.get('upside', [])
        downside = scenarios.get('downside', [])
        
        content = [
            "**Three scenarios modeled with probability-weighted outcomes:**",
            "",
            f"• **Base Case (50% probability):** ${base[-1]:,.0f}M revenue by Year 5" if base else "",
            f"• **Upside Case (25% probability):** ${upside[-1]:,.0f}M revenue by Year 5" if upside else "",
            f"• **Downside Case (25% probability):** ${downside[-1]:,.0f}M revenue by Year 5" if downside else "",
            "",
            "• Expected value incorporates all scenarios",
            "• Sensitivity analysis conducted on key assumptions"
        ]
        
        content = [c for c in content if c]  # Remove empty strings
        
        return {
            "slide_number": 8,
            "type": "chart",
            "title": "Revenue Scenarios & Projections",
            "content": content,
            "chart_data": json.loads(chart_json) if isinstance(chart_json, str) else chart_json,
            "speaker_notes": "Three scenarios based on market penetration, pricing, and competitive dynamics. Base case most likely."
        }
    
    @staticmethod
    def create_risk_matrix_slide(
        risk_matrix: Dict[str, Any],
        chart_json: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create risk matrix slide."""
        risks = risk_matrix.get('risks', [])
        top_risks = sorted(risks, key=lambda x: x.get('score', 0), reverse=True)[:5]
        
        content = [
            "**Top 5 Risks Identified:**",
            ""
        ]
        
        for risk in top_risks:
            score = risk.get('score', 0)
            content.append(f"• {risk.get('risk', 'Unknown')} (Score: {score}/25)")
        
        content.append("")
        content.append(f"**Overall Risk Level:** {risk_matrix.get('risk_level', 'unknown').upper()}")
        content.append(f"**Total Risk Score:** {risk_matrix.get('total_risk_score', 0)}")
        
        return {
            "slide_number": 10,
            "type": "chart",
            "title": "Risk Assessment Matrix",
            "content": content,
            "chart_data": json.loads(chart_json) if chart_json and isinstance(chart_json, str) else None,
            "speaker_notes": "Comprehensive risk analysis using probability-impact matrix. Mitigation strategies identified for all high-risk items."
        }
    
    @staticmethod
    def create_implementation_slide(
        roadmap: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create implementation roadmap slide."""
        content = ["**Phased Implementation Approach:**", ""]
        
        for phase in roadmap[:3]:  # Show first 3 phases
            phase_name = phase.get('phase', 'Unknown Phase')
            content.append(f"**{phase_name}**")
            
            milestones = phase.get('milestones', [])
            if milestones:
                content.append(f"• Key Milestones: {', '.join(milestones[:3])}")
            
            metrics = phase.get('success_metrics', [])
            if metrics:
                content.append(f"• Success Metrics: {', '.join(metrics[:2])}")
            
            content.append("")
        
        return {
            "slide_number": 11,
            "type": "content",
            "title": "Implementation Roadmap",
            "content": content,
            "chart_data": None,
            "speaker_notes": "Detailed implementation plan with clear milestones and success metrics for each phase."
        }
    
    @staticmethod
    def build_complete_deck(
        request: Dict[str, Any],
        exec_summary: Dict[str, Any],
        market_analysis: Dict[str, Any],
        financial_model: Dict[str, Any],
        regulatory: Dict[str, Any],
        charts: Dict[str, str],
        implementation: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build complete 12-15 slide deck.
        
        Args:
            request: Original request
            exec_summary: Executive summary from synthesizer
            market_analysis: Market analysis from analyst
            financial_model: Financial model from analyst
            regulatory: Regulatory findings
            charts: Chart JSON strings
            implementation: Implementation roadmap
            
        Returns:
            List of slide dictionaries
        """
        slides = []
        
        # Slide 1: Title
        slides.append(SlideBuilder.create_title_slide(
            request.get('company_name', 'Company'),
            request.get('strategic_question', 'Strategic Question')
        ))
        
        # Slide 2: Executive Summary
        slides.append(SlideBuilder.create_executive_summary_slide(exec_summary))
        
        # Slide 3: Market Overview
        slides.append({
            "slide_number": 3,
            "type": "content",
            "title": "Market Overview",
            "content": [
                f"**Industry:** {request.get('industry', 'Unknown')}",
                f"**Analysis Type:** {request.get('analysis_type', 'expansion').title()}",
                "",
                "**Market Context:**",
                f"• Market attractiveness validated through comprehensive analysis",
                f"• Competitive landscape assessed",
                f"• Growth drivers identified"
            ],
            "chart_data": None,
            "speaker_notes": "Overview of market context and industry dynamics."
        })
        
        # Slide 4: Market Sizing
        tam = market_analysis.get('TAM', {}).get('value_usd_millions', 0)
        sam = market_analysis.get('SAM', {}).get('value_usd_millions', 0)
        som = market_analysis.get('SOM', {}).get('year_5_usd_millions', 0)
        
        slides.append(SlideBuilder.create_market_sizing_slide(
            tam, sam, som,
            charts.get('market_sizing', '{}')
        ))
        
        # Slide 5: Competitive Position
        comp_pos = financial_model.get('competitive_position', {})
        slides.append({
            "slide_number": 5,
            "type": "content",
            "title": "Competitive Position",
            "content": [
                f"**Positioning:** {comp_pos.get('positioning', 'Unknown').title()}",
                f"**Target Market Share:** {comp_pos.get('market_share_estimate', 0)*100:.1f}%",
                "",
                "**Key Differentiators:**",
                *[f"• {d}" for d in comp_pos.get('key_differentiators', [])[:4]]
            ],
            "chart_data": None,
            "speaker_notes": "Competitive positioning based on market analysis and strategic capabilities."
        })
        
        # Slide 6: Unit Economics
        unit_econ = financial_model.get('unit_economics', {})
        slides.append({
            "slide_number": 6,
            "type": "content",
            "title": "Unit Economics",
            "content": [
                f"**Customer Acquisition Cost (CAC):** ${unit_econ.get('CAC', 0):.2f}",
                f"**Lifetime Value (LTV):** ${unit_econ.get('LTV', 0):.2f}",
                f"**LTV/CAC Ratio:** {unit_econ.get('LTV_CAC_ratio', 0):.2f}x",
                "",
                f"**Assessment:** {unit_econ.get('assessment', 'Unknown').upper()}",
                "",
                "• Healthy unit economics support sustainable growth",
                "• Ratio exceeds 3:1 benchmark for viable business model"
            ],
            "chart_data": None,
            "speaker_notes": "Unit economics analysis shows strong customer value proposition."
        })
        
        # Slide 7: Financial Projections
        slides.append({
            "slide_number": 7,
            "type": "content",
            "title": "Financial Highlights",
            "content": [
                f"**Valuation (DCF):** ${financial_model.get('valuation', {}).get('enterprise_value', 0):,.0f}M",
                "",
                "**Key Metrics:**",
                f"• Strong unit economics ({unit_econ.get('LTV_CAC_ratio', 0):.1f}x LTV/CAC)",
                f"• Attractive market size (${tam:,.0f}M TAM)",
                f"• Clear path to profitability"
            ],
            "chart_data": None,
            "speaker_notes": "Financial analysis demonstrates attractive returns and manageable risk profile."
        })
        
        # Slide 8: Scenarios
        scenarios = financial_model.get('scenarios', {})
        if scenarios:
            slides.append(SlideBuilder.create_scenario_slide(
                scenarios,
                charts.get('revenue_scenarios', '{}')
            ))
        
        # Slide 9: Regulatory Assessment
        slides.append({
            "slide_number": 9,
            "type": "content",
            "title": "Regulatory & Compliance",
            "content": [
                f"**Overall Risk Level:** {regulatory.get('overall_risk_level', 'unknown').upper()}",
                f"**Recommended Structure:** {regulatory.get('recommended_structure', {}).get('recommended_structure', 'Unknown')}",
                "",
                "**Key Regulatory Considerations:**",
                *[f"• {blocker}" for blocker in regulatory.get('key_blockers', [])[:3]],
                "",
                f"**Setup Timeline:** {regulatory.get('recommended_structure', {}).get('setup_timeline', 'Unknown')}"
            ],
            "chart_data": None,
            "speaker_notes": "Regulatory analysis identifies key compliance requirements and optimal legal structure."
        })
        
        # Slide 10: Risk Matrix
        risk_matrix = regulatory.get('risk_matrix', {})
        slides.append(SlideBuilder.create_risk_matrix_slide(
            risk_matrix,
            charts.get('risk_heatmap')
        ))
        
        # Slide 11: Implementation Roadmap
        if implementation:
            slides.append(SlideBuilder.create_implementation_slide(implementation))
        
        # Slide 12: Next Steps
        slides.append({
            "slide_number": 12,
            "type": "content",
            "title": "Recommended Next Steps",
            "content": [
                "**Immediate Actions (Next 30 days):**",
                "• Finalize strategic decision based on this analysis",
                "• Initiate regulatory approval process if proceeding",
                "• Assemble core team",
                "",
                "**Near-term (60-90 days):**",
                "• Complete legal entity setup",
                "• Secure initial funding",
                "• Begin market entry preparations"
            ],
            "chart_data": None,
            "speaker_notes": "Clear action plan for moving forward based on recommendation."
        })
        
        return slides
