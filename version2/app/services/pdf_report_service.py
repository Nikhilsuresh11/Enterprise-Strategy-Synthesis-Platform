"""PDF Report Generation Service."""

from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PDFReportService:
    """
    Service for generating PDF analysis reports.
    
    Creates professional PDF documents with:
    - Executive summary
    - Company profile
    - Market analysis
    - Financial highlights
    - Risk assessment
    - Strategic recommendations
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        logger.info("pdf_report_service_initialized")
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor='#1E40AF',
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor='#1E40AF',
            spaceAfter=12,
            spaceBefore=20
        ))
        
        # Bullet point
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=20,
            spaceAfter=8
        ))
    
    async def generate_report(
        self,
        company_name: str,
        analysis_data: Dict[str, Any],
        output_path: str
    ):
        """
        Generate PDF report from analysis data.
        
        Args:
            company_name: Name of analyzed company
            analysis_data: Complete analysis state
            output_path: Path to save PDF
        """
        logger.info("generating_pdf_report", company=company_name, path=output_path)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph(
            f"{company_name} Strategic Analysis",
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 0.3 * inch))
        
        # Executive Summary
        strategy = analysis_data.get("strategy_synthesis", {})
        if strategy.get("executive_summary"):
            story.append(Paragraph("Executive Summary", self.styles['SectionHeading']))
            story.append(Paragraph(strategy["executive_summary"], self.styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
        
        # Company Profile
        profile = analysis_data.get("company_profile", {})
        if profile.get("key_facts"):
            story.append(Paragraph("Company Overview", self.styles['SectionHeading']))
            for fact in profile["key_facts"]:
                story.append(Paragraph(f"• {fact}", self.styles['BulletPoint']))
            story.append(Spacer(1, 0.2 * inch))
        
        # Market Analysis
        market = analysis_data.get("market_analysis", {})
        if market.get("key_insights"):
            story.append(Paragraph("Market Insights", self.styles['SectionHeading']))
            for insight in market["key_insights"]:
                story.append(Paragraph(f"• {insight}", self.styles['BulletPoint']))
            story.append(Spacer(1, 0.2 * inch))
        
        # Financial Highlights
        financial = analysis_data.get("financial_model", {})
        if financial.get("key_highlights"):
            story.append(Paragraph("Financial Highlights", self.styles['SectionHeading']))
            for highlight in financial["key_highlights"]:
                story.append(Paragraph(f"• {highlight}", self.styles['BulletPoint']))
            story.append(Spacer(1, 0.2 * inch))
        
        # Risk Assessment
        risks = analysis_data.get("risk_assessment", {})
        if risks.get("top_risks"):
            story.append(Paragraph("Key Risks", self.styles['SectionHeading']))
            for risk in risks["top_risks"]:
                risk_text = f"• [{risk.get('severity', 'Medium')}] {risk.get('risk', '')}: {risk.get('description', '')}"
                story.append(Paragraph(risk_text, self.styles['BulletPoint']))
            story.append(Spacer(1, 0.2 * inch))
        
        # Strategic Recommendations
        if strategy.get("key_recommendations"):
            story.append(PageBreak())
            story.append(Paragraph("Strategic Recommendations", self.styles['SectionHeading']))
            for rec in strategy["key_recommendations"]:
                story.append(Paragraph(f"• {rec}", self.styles['BulletPoint']))
            story.append(Spacer(1, 0.2 * inch))
        
        # SWOT Summary
        swot = strategy.get("swot_summary", {})
        if swot:
            story.append(Paragraph("SWOT Analysis", self.styles['SectionHeading']))
            if swot.get("top_strength"):
                story.append(Paragraph(f"<b>Strength:</b> {swot['top_strength']}", self.styles['Normal']))
            if swot.get("top_weakness"):
                story.append(Paragraph(f"<b>Weakness:</b> {swot['top_weakness']}", self.styles['Normal']))
            if swot.get("top_opportunity"):
                story.append(Paragraph(f"<b>Opportunity:</b> {swot['top_opportunity']}", self.styles['Normal']))
            if swot.get("top_threat"):
                story.append(Paragraph(f"<b>Threat:</b> {swot['top_threat']}", self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        logger.info("pdf_report_generated", company=company_name, path=output_path)
