"""PDF generation service using ReportLab."""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from io import BytesIO
from typing import List, Dict, Any
from datetime import datetime
import plotly.graph_objects as go
import os


class PDFGenerator:
    """Generate consulting-grade PDF decks."""
    
    def __init__(self):
        """Initialize PDF generator with custom styles."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Create consulting-grade styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ConsultingTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Slide title style
        self.styles.add(ParagraphStyle(
            name='SlideTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Bullet point style
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=20,
            spaceAfter=8,
            textColor=colors.HexColor('#374151'),
            fontName='Helvetica'
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
    
    async def generate_pdf(
        self,
        slides: List[Dict[str, Any]],
        output_path: str,
        company_name: str
    ) -> str:
        """
        Generate consulting-style PDF from slides.
        
        Args:
            slides: List of slide dictionaries
            output_path: Path to save PDF
            company_name: Company name for footer
            
        Returns:
            Path to generated PDF
        """
        try:
            # Create document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.75*inch
            )
            
            story = []
            
            # Generate each slide
            for slide in slides:
                slide_type = slide.get('type', 'content')
                
                if slide_type == 'title':
                    story.extend(self._create_title_slide(slide))
                elif slide_type == 'chart':
                    story.extend(self._create_chart_slide(slide))
                else:
                    story.extend(self._create_content_slide(slide))
                
                # Page break after each slide
                story.append(PageBreak())
            
            # Build PDF with footer
            doc.build(
                story,
                onFirstPage=lambda c, d: self._add_footer(c, d, company_name),
                onLaterPages=lambda c, d: self._add_footer(c, d, company_name)
            )
            
            return output_path
            
        except Exception as e:
            print(f"PDF generation failed: {e}")
            raise
    
    def _create_title_slide(self, slide: Dict[str, Any]) -> List:
        """Create title slide."""
        elements = []
        
        # Spacer
        elements.append(Spacer(1, 2*inch))
        
        # Main title
        title = Paragraph(slide.get('title', ''), self.styles['ConsultingTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # Subtitle
        if slide.get('subtitle'):
            subtitle = Paragraph(slide['subtitle'], self.styles['Normal'])
            elements.append(subtitle)
            elements.append(Spacer(1, 0.3*inch))
        
        # Date
        date_text = f"Generated: {datetime.now().strftime('%B %d, %Y')}"
        date = Paragraph(date_text, self.styles['Footer'])
        elements.append(Spacer(1, 3*inch))
        elements.append(date)
        
        return elements
    
    def _create_content_slide(self, slide: Dict[str, Any]) -> List:
        """Create content slide with bullets."""
        elements = []
        
        # Slide title
        title = Paragraph(slide.get('title', ''), self.styles['SlideTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Content bullets
        for item in slide.get('content', []):
            if isinstance(item, str) and item.strip():
                # Clean up bullet formatting
                clean_item = item.replace('•', '').strip()
                if clean_item.startswith('**') and '**' in clean_item[2:]:
                    # Bold text handling
                    clean_item = clean_item.replace('**', '<b>', 1).replace('**', '</b>', 1)
                
                bullet = Paragraph(f"• {clean_item}", self.styles['BulletPoint'])
                elements.append(bullet)
        
        return elements
    
    def _create_chart_slide(self, slide: Dict[str, Any]) -> List:
        """Create slide with chart."""
        elements = []
        
        # Title
        title = Paragraph(slide.get('title', ''), self.styles['SlideTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Chart (convert Plotly to image)
        chart_data = slide.get('chart_data')
        if chart_data:
            chart_img = self._plotly_to_image(chart_data)
            if chart_img:
                elements.append(chart_img)
                elements.append(Spacer(1, 0.2*inch))
        
        # Content bullets
        for item in slide.get('content', []):
            if isinstance(item, str) and item.strip():
                clean_item = item.replace('•', '').strip()
                bullet = Paragraph(f"• {clean_item}", self.styles['BulletPoint'])
                elements.append(bullet)
        
        return elements
    
    def _plotly_to_image(self, chart_data: Dict, width: float = 6*inch, height: float = 4*inch):
        """Convert Plotly chart to ReportLab image."""
        try:
            # Create figure from data
            fig = go.Figure(chart_data)
            
            # Convert to PNG bytes
            img_bytes = fig.to_image(format="png", width=int(width*1.5), height=int(height*1.5))
            
            # Create ReportLab image
            img_buffer = BytesIO(img_bytes)
            img = Image(img_buffer, width=width, height=height)
            return img
            
        except Exception as e:
            print(f"Chart conversion failed: {e}")
            return None
    
    def _add_footer(self, canvas, doc, company_name: str):
        """Add footer to each page."""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        
        # Page number
        page_text = f"Stratagem AI | {company_name} | Page {doc.page}"
        canvas.drawCentredString(
            4.25*inch,
            0.4*inch,
            page_text
        )
        
        canvas.restoreState()
