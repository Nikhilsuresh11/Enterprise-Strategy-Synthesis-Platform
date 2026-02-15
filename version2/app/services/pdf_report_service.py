"""PDF Report Generation Service."""

from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
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

    async def generate_comparison_report(
        self,
        title: str,
        companies: List[str],
        comparison_data: Dict[str, Any],
        output_path: str,
    ):
        """Generate a comparison PDF with side-by-side tables."""
        logger.info("generating_comparison_pdf", companies=companies, path=output_path)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=60,
            bottomMargin=30,
        )

        story = []

        # Title
        story.append(Paragraph(title, self.styles["CustomTitle"]))
        story.append(Spacer(1, 0.3 * inch))

        # Each category → a table
        categories = comparison_data.get("categories", [])

        for cat in categories:
            cat_name = cat.get("name", "")
            rows_data = cat.get("rows", [])
            if not rows_data:
                continue

            story.append(Paragraph(cat_name, self.styles["SectionHeading"]))

            # Build header row
            header = ["Metric"] + companies
            table_rows = [header]

            for row in rows_data:
                metric = row.get("metric", "")
                vals = [metric]
                for i in range(len(companies)):
                    vals.append(str(row.get(f"company_{i}", "N/A")))
                table_rows.append(vals)

            # Calculate column widths
            avail = 6.5 * inch
            metric_w = avail * 0.3
            company_w = (avail * 0.7) / max(len(companies), 1)
            col_widths = [metric_w] + [company_w] * len(companies)

            t = Table(table_rows, colWidths=col_widths)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.2 * inch))

        # Verdict
        verdict = comparison_data.get("verdict", "")
        if verdict:
            story.append(PageBreak())
            story.append(Paragraph("Verdict", self.styles["SectionHeading"]))
            story.append(Paragraph(verdict, self.styles["Normal"]))

        doc.build(story)
        logger.info("comparison_pdf_generated", path=output_path)

