"""Production-grade PDF generation service using ReportLab.

Designed to match McKinsey, BCG, Bain, and JPMorgan visual standards.
Incorporates professional branding, advanced layouts, and consulting-grade aesthetics.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle,
    KeepTogether, PageTemplate, Frame
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from io import BytesIO
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import plotly.graph_objects as go
import os


class PDFGenerator:
    """Generate McKinsey/BCG/JPM-grade PDF decks with professional branding."""
    
    # Professional color palettes
    BRAND_COLORS = {
        'mckinsey': {
            'primary': colors.HexColor('#003F5C'),      # Deep blue
            'accent': colors.HexColor('#2F4B7C'),       # Teal
            'highlight': colors.HexColor('#F95D6A'),    # Coral
            'secondary': colors.HexColor('#A05195'),    # Purple-blue
            'neutral': colors.HexColor('#665191'),      # Gray-purple
            'background': colors.HexColor('#FFFFFF'),   # White
            'text_dark': colors.HexColor('#1A1A1A'),   # Near black
            'text_light': colors.HexColor('#666666')   # Medium gray
        },
        'bcg': {
            'primary': colors.HexColor('#00A758'),      # BCG green
            'accent': colors.HexColor('#003F5C'),       # Dark blue
            'highlight': colors.HexColor('#FF6F3C'),    # Orange
            'secondary': colors.HexColor('#58B4D9'),    # Light blue
            'neutral': colors.HexColor('#8B8B8B'),      # Gray
            'background': colors.HexColor('#FFFFFF'),   # White
            'text_dark': colors.HexColor('#000000'),    # Black
            'text_light': colors.HexColor('#4A4A4A')    # Dark gray
        },
        'jpmorgan': {
            'primary': colors.HexColor('#005EB8'),      # JPM blue
            'accent': colors.HexColor('#333333'),       # Dark gray
            'highlight': colors.HexColor('#D4AF37'),    # Gold
            'secondary': colors.HexColor('#CCCCCC'),    # Light gray
            'neutral': colors.HexColor('#999999'),      # Medium gray
            'background': colors.HexColor('#FFFFFF'),   # White
            'text_dark': colors.HexColor('#000000'),    # Black
            'text_light': colors.HexColor('#666666')    # Medium gray
        },
        'bain': {
            'primary': colors.HexColor('#ED1C24'),      # Bain red
            'accent': colors.HexColor('#1F2937'),       # Dark gray
            'highlight': colors.HexColor('#F59E0B'),    # Amber
            'secondary': colors.HexColor('#3B82F6'),    # Blue
            'neutral': colors.HexColor('#6B7280'),      # Gray
            'background': colors.HexColor('#FFFFFF'),   # White
            'text_dark': colors.HexColor('#111827'),    # Near black
            'text_light': colors.HexColor('#6B7280')    # Medium gray
        }
    }
    
    def __init__(self, brand: str = 'mckinsey'):
        """
        Initialize PDF generator with brand-specific styling.
        
        Args:
            brand: Brand theme ('mckinsey', 'bcg', 'jpmorgan', 'bain')
        """
        self.brand = brand.lower()
        self.colors = self.BRAND_COLORS.get(self.brand, self.BRAND_COLORS['mckinsey'])
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.toc_entries = []  # For table of contents
    
    def _setup_custom_styles(self):
        """Create consulting-grade styles with brand colors."""
        
        # Cover page title
        self.styles.add(ParagraphStyle(
            name='CoverTitle',
            parent=self.styles['Heading1'],
            fontSize=44,
            textColor=self.colors['primary'],
            spaceAfter=30,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=52
        ))
        
        # Cover subtitle
        self.styles.add(ParagraphStyle(
            name='CoverSubtitle',
            parent=self.styles['Normal'],
            fontSize=24,
            textColor=self.colors['text_light'],
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=30
        ))
        
        # Section title (for dividers)
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading1'],
            fontSize=36,
            textColor=self.colors['primary'],
            spaceAfter=20,
            spaceBefore=100,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            leading=42,
            borderPadding=(10, 0, 10, 0),
            leftIndent=0
        ))
        
        # Slide title
        self.styles.add(ParagraphStyle(
            name='SlideTitle',
            parent=self.styles['Heading2'],
            fontSize=22,
            textColor=self.colors['text_dark'],
            spaceAfter=16,
            spaceBefore=0,
            fontName='Helvetica-Bold',
            leading=26,
            borderWidth=0,
            borderColor=self.colors['primary'],
            borderPadding=0
        ))
        
        # Slide subtitle
        self.styles.add(ParagraphStyle(
            name='SlideSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=self.colors['text_light'],
            spaceAfter=12,
            fontName='Helvetica-Oblique',
            leading=18
        ))
        
        # Body text
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=self.colors['text_dark'],
            spaceAfter=10,
            fontName='Helvetica',
            leading=16,
            alignment=TA_JUSTIFY
        ))
        
        # Bullet point (level 1)
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontSize=12,
            leftIndent=20,
            spaceAfter=8,
            textColor=self.colors['text_dark'],
            fontName='Helvetica',
            leading=16,
            bulletIndent=10
        ))
        
        # Bullet point (level 2)
        self.styles.add(ParagraphStyle(
            name='BulletPoint2',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=40,
            spaceAfter=6,
            textColor=self.colors['text_dark'],
            fontName='Helvetica',
            leading=14,
            bulletIndent=30
        ))
        
        # Callout box text
        self.styles.add(ParagraphStyle(
            name='CalloutText',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.colors['text_dark'],
            spaceAfter=8,
            fontName='Helvetica-Bold',
            leading=14,
            alignment=TA_LEFT
        ))
        
        # Pull quote
        self.styles.add(ParagraphStyle(
            name='PullQuote',
            parent=self.styles['Normal'],
            fontSize=16,
            textColor=self.colors['primary'],
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Oblique',
            leading=22,
            alignment=TA_CENTER,
            leftIndent=40,
            rightIndent=40
        ))
        
        # Caption
        self.styles.add(ParagraphStyle(
            name='Caption',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=self.colors['text_light'],
            spaceAfter=6,
            fontName='Helvetica',
            leading=11,
            alignment=TA_CENTER
        ))
        
        # Footer
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=self.colors['text_light'],
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=10
        ))
        
        # TOC entry
        self.styles.add(ParagraphStyle(
            name='TOCEntry',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=self.colors['text_dark'],
            spaceAfter=8,
            fontName='Helvetica',
            leading=16
        ))
    
    async def generate_pdf(
        self,
        slides: List[Dict[str, Any]],
        output_path: str,
        company_name: str,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        include_toc: bool = True,
        include_executive_summary: bool = True,
        executive_summary: Optional[Dict] = None
    ) -> str:
        """
        Generate consulting-style PDF from slides.
        
        Args:
            slides: List of slide dictionaries
            output_path: Path to save PDF
            company_name: Company name for footer
            title: Document title (for cover page)
            subtitle: Document subtitle
            include_toc: Include table of contents
            include_executive_summary: Include executive summary page
            executive_summary: Executive summary content
            
        Returns:
            Path to generated PDF
        """
        try:
            # Create document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=1*inch
            )
            
            story = []
            
            # Cover page
            if title:
                story.extend(self._create_cover_page(title, subtitle, company_name))
                story.append(PageBreak())
            
            # Table of contents
            if include_toc:
                story.extend(self._create_table_of_contents(slides))
                story.append(PageBreak())
            
            # Executive summary
            if include_executive_summary and executive_summary:
                story.extend(self._create_executive_summary_page(executive_summary))
                story.append(PageBreak())
            
            # Generate each slide
            for idx, slide in enumerate(slides, 1):
                slide_type = slide.get('type', 'content')
                
                # Add to TOC
                if slide.get('title'):
                    self.toc_entries.append({
                        'title': slide['title'],
                        'page': idx + (2 if include_toc else 1)
                    })
                
                if slide_type == 'title':
                    story.extend(self._create_title_slide(slide))
                elif slide_type == 'section_divider':
                    story.extend(self._create_section_divider(slide))
                elif slide_type == 'chart':
                    story.extend(self._create_chart_slide(slide))
                elif slide_type == 'two_column':
                    story.extend(self._create_two_column_slide(slide))
                elif slide_type == 'comparison':
                    story.extend(self._create_comparison_slide(slide))
                else:
                    story.extend(self._create_content_slide(slide))
                
                # Page break after each slide
                story.append(PageBreak())
            
            # Build PDF with custom footer
            doc.build(
                story,
                onFirstPage=lambda c, d: self._add_page_elements(c, d, company_name, is_first=True),
                onLaterPages=lambda c, d: self._add_page_elements(c, d, company_name, is_first=False)
            )
            
            return output_path
            
        except Exception as e:
            print(f"PDF generation failed: {e}")
            raise
    
    def _create_cover_page(self, title: str, subtitle: Optional[str], company_name: str) -> List:
        """Create professional cover page."""
        elements = []
        
        # Top spacer
        elements.append(Spacer(1, 2.5*inch))
        
        # Brand accent bar
        elements.append(self._create_accent_bar())
        elements.append(Spacer(1, 0.5*inch))
        
        # Main title
        title_para = Paragraph(title, self.styles['CoverTitle'])
        elements.append(title_para)
        elements.append(Spacer(1, 0.3*inch))
        
        # Subtitle
        if subtitle:
            subtitle_para = Paragraph(subtitle, self.styles['CoverSubtitle'])
            elements.append(subtitle_para)
            elements.append(Spacer(1, 0.5*inch))
        
        # Company name
        company_para = Paragraph(
            f"<b>{company_name}</b>",
            self.styles['CoverSubtitle']
        )
        elements.append(Spacer(1, 2*inch))
        elements.append(company_para)
        
        # Date
        date_text = datetime.now().strftime('%B %d, %Y')
        date_para = Paragraph(date_text, self.styles['Footer'])
        elements.append(Spacer(1, 0.2*inch))
        elements.append(date_para)
        
        return elements
    
    def _create_table_of_contents(self, slides: List[Dict]) -> List:
        """Create table of contents page."""
        elements = []
        
        # Title
        toc_title = Paragraph("Table of Contents", self.styles['SectionTitle'])
        elements.append(toc_title)
        elements.append(Spacer(1, 0.3*inch))
        
        # TOC entries
        for idx, slide in enumerate(slides, 1):
            if slide.get('title') and slide.get('type') != 'title':
                # Create dotted line entry
                title_text = slide['title'][:80]  # Truncate long titles
                entry = Paragraph(
                    f"{idx}. {title_text}",
                    self.styles['TOCEntry']
                )
                elements.append(entry)
        
        return elements
    
    def _create_executive_summary_page(self, summary: Dict) -> List:
        """Create executive summary page."""
        elements = []
        
        # Title
        title = Paragraph("Executive Summary", self.styles['SectionTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Key insight callout
        if summary.get('key_insight'):
            callout = self._create_callout_box(
                summary['key_insight'],
                box_type='insight'
            )
            elements.extend(callout)
            elements.append(Spacer(1, 0.2*inch))
        
        # Recommendations
        if summary.get('recommendations'):
            rec_title = Paragraph("<b>Key Recommendations</b>", self.styles['BodyText'])
            elements.append(rec_title)
            elements.append(Spacer(1, 0.1*inch))
            
            for rec in summary['recommendations'][:5]:  # Top 5
                bullet = Paragraph(f"• {rec}", self.styles['BulletPoint'])
                elements.append(bullet)
        
        return elements
    
    def _create_section_divider(self, slide: Dict) -> List:
        """Create section divider slide."""
        elements = []
        
        # Spacer
        elements.append(Spacer(1, 2*inch))
        
        # Colored bar
        elements.append(self._create_accent_bar())
        elements.append(Spacer(1, 0.5*inch))
        
        # Section title
        title = Paragraph(slide.get('title', ''), self.styles['SectionTitle'])
        elements.append(title)
        
        # Section description
        if slide.get('description'):
            desc = Paragraph(slide['description'], self.styles['BodyText'])
            elements.append(Spacer(1, 0.3*inch))
            elements.append(desc)
        
        return elements
    
    def _create_title_slide(self, slide: Dict[str, Any]) -> List:
        """Create title slide."""
        elements = []
        
        # Spacer
        elements.append(Spacer(1, 2*inch))
        
        # Main title
        title = Paragraph(slide.get('title', ''), self.styles['CoverTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # Subtitle
        if slide.get('subtitle'):
            subtitle = Paragraph(slide['subtitle'], self.styles['CoverSubtitle'])
            elements.append(subtitle)
        
        return elements
    
    def _create_content_slide(self, slide: Dict[str, Any]) -> List:
        """Create content slide with bullets."""
        elements = []
        
        # Slide title
        title = Paragraph(slide.get('title', ''), self.styles['SlideTitle'])
        elements.append(title)
        
        # Subtitle if present
        if slide.get('subtitle'):
            subtitle = Paragraph(slide['subtitle'], self.styles['SlideSubtitle'])
            elements.append(subtitle)
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Content bullets
        for item in slide.get('content', []):
            if isinstance(item, str) and item.strip():
                # Determine bullet level
                level = 0
                clean_item = item.strip()
                
                # Check for indentation markers
                if clean_item.startswith('  -') or clean_item.startswith('    •'):
                    level = 1
                    clean_item = clean_item.lstrip(' -•').strip()
                else:
                    clean_item = clean_item.lstrip('•-').strip()
                
                # Handle bold text
                if clean_item.startswith('**') and '**' in clean_item[2:]:
                    clean_item = clean_item.replace('**', '<b>', 1).replace('**', '</b>', 1)
                
                # Select style based on level
                style = self.styles['BulletPoint2'] if level == 1 else self.styles['BulletPoint']
                bullet_char = '◦' if level == 1 else '•'
                
                bullet = Paragraph(f"{bullet_char} {clean_item}", style)
                elements.append(bullet)
        
        return elements
    
    def _create_two_column_slide(self, slide: Dict) -> List:
        """Create two-column layout slide."""
        elements = []
        
        # Title
        title = Paragraph(slide.get('title', ''), self.styles['SlideTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Create table for two columns
        left_content = slide.get('left_column', [])
        right_content = slide.get('right_column', [])
        
        # Build column content
        left_items = []
        for item in left_content:
            if isinstance(item, str):
                left_items.append(Paragraph(f"• {item}", self.styles['BulletPoint']))
        
        right_items = []
        for item in right_content:
            if isinstance(item, str):
                right_items.append(Paragraph(f"• {item}", self.styles['BulletPoint']))
        
        # Create table
        data = [[left_items, right_items]]
        table = Table(data, colWidths=[3.25*inch, 3.25*inch])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_comparison_slide(self, slide: Dict) -> List:
        """Create comparison slide (e.g., before/after, options)."""
        elements = []
        
        # Title
        title = Paragraph(slide.get('title', ''), self.styles['SlideTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Comparison table
        options = slide.get('options', [])
        if len(options) >= 2:
            # Create comparison table
            table_data = []
            
            # Headers
            headers = [Paragraph(f"<b>{opt.get('name', '')}</b>", self.styles['BodyText']) 
                      for opt in options]
            table_data.append(headers)
            
            # Pros
            pros_row = []
            for opt in options:
                pros = opt.get('pros', [])
                pros_text = '<br/>'.join([f"✓ {p}" for p in pros[:3]])
                pros_row.append(Paragraph(pros_text, self.styles['Caption']))
            table_data.append(pros_row)
            
            # Cons
            cons_row = []
            for opt in options:
                cons = opt.get('cons', [])
                cons_text = '<br/>'.join([f"✗ {c}" for c in cons[:3]])
                cons_row.append(Paragraph(cons_text, self.styles['Caption']))
            table_data.append(cons_row)
            
            # Create table
            col_width = 6.5*inch / len(options)
            table = Table(table_data, colWidths=[col_width] * len(options))
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 0.5, self.colors['neutral']),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
            ]))
            
            elements.append(table)
        
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
            chart_img = self._plotly_to_image(
                chart_data,
                width=6*inch,
                height=3.5*inch,
                dpi=300  # High resolution
            )
            if chart_img:
                elements.append(chart_img)
                elements.append(Spacer(1, 0.2*inch))
                
                # Chart caption
                if slide.get('chart_caption'):
                    caption = Paragraph(slide['chart_caption'], self.styles['Caption'])
                    elements.append(caption)
                    elements.append(Spacer(1, 0.2*inch))
        
        # Content bullets (key insights)
        for item in slide.get('content', []):
            if isinstance(item, str) and item.strip():
                clean_item = item.replace('•', '').strip()
                bullet = Paragraph(f"• {clean_item}", self.styles['BulletPoint'])
                elements.append(bullet)
        
        return elements
    
    def _create_callout_box(self, text: str, box_type: str = 'insight') -> List:
        """Create colored callout box."""
        elements = []
        
        # Select color based on type
        box_colors = {
            'insight': self.colors['highlight'],
            'warning': colors.HexColor('#EF4444'),
            'success': colors.HexColor('#10B981'),
            'info': self.colors['accent']
        }
        box_color = box_colors.get(box_type, self.colors['highlight'])
        
        # Create table for callout
        content = Paragraph(text, self.styles['CalloutText'])
        data = [[content]]
        table = Table(data, colWidths=[6.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), box_color.clone(alpha=0.1)),
            ('BOX', (0, 0), (-1, -1), 2, box_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_accent_bar(self) -> Table:
        """Create colored accent bar."""
        data = [['']]
        table = Table(data, colWidths=[6.5*inch], rowHeights=[0.15*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.colors['primary']),
        ]))
        return table
    
    def _plotly_to_image(
        self,
        chart_data: Dict,
        width: float = 6*inch,
        height: float = 4*inch,
        dpi: int = 300
    ):
        """Convert Plotly chart to high-resolution ReportLab image."""
        try:
            # Create figure from data
            fig = go.Figure(chart_data)
            
            # Apply brand colors to chart
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Helvetica', size=11, color=str(self.colors['text_dark'])),
                title_font=dict(size=14, color=str(self.colors['primary'])),
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            # Convert to PNG bytes with high DPI
            img_bytes = fig.to_image(
                format="png",
                width=int(width * dpi / 72),
                height=int(height * dpi / 72),
                scale=2
            )
            
            # Create ReportLab image
            img_buffer = BytesIO(img_bytes)
            img = Image(img_buffer, width=width, height=height)
            return img
            
        except Exception as e:
            print(f"Chart conversion failed: {e}")
            return None
    
    def _add_page_elements(self, canvas, doc, company_name: str, is_first: bool = False):
        """Add header, footer, and page number to each page."""
        canvas.saveState()
        
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(self.colors['text_light'])
        
        # Left: Brand name
        canvas.drawString(
            0.75*inch,
            0.5*inch,
            f"{self.brand.upper()} | {company_name}"
        )
        
        # Center: Confidential
        canvas.drawCentredString(
            4.25*inch,
            0.5*inch,
            "CONFIDENTIAL"
        )
        
        # Right: Page number
        if not is_first:
            canvas.drawRightString(
                7.75*inch,
                0.5*inch,
                f"Page {doc.page}"
            )
        
        # Top accent line
        canvas.setStrokeColor(self.colors['primary'])
        canvas.setLineWidth(2)
        canvas.line(0.75*inch, 10.5*inch, 7.75*inch, 10.5*inch)
        
        canvas.restoreState()

    
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
