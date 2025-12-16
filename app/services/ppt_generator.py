"""PowerPoint generation service using python-pptx."""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from typing import List, Dict, Any
import plotly.graph_objects as go
from io import BytesIO


class PPTGenerator:
    """Generate consulting-grade PowerPoint presentations."""
    
    def __init__(self):
        """Initialize PPT generator."""
        self.prs = Presentation()
        self.prs.slide_width = Inches(10)
        self.prs.slide_height = Inches(7.5)
        
        # Define consulting color scheme
        self.colors = {
            'primary': RGBColor(31, 41, 55),  # Dark gray
            'accent': RGBColor(59, 130, 246),  # Blue
            'text': RGBColor(55, 65, 81)  # Medium gray
        }
    
    async def generate_ppt(
        self,
        slides: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        Generate PowerPoint presentation.
        
        Args:
            slides: List of slide dictionaries
            output_path: Path to save PPTX
            
        Returns:
            Path to generated PPTX
        """
        try:
            for slide_data in slides:
                slide_type = slide_data.get('type', 'content')
                
                if slide_type == 'title':
                    self._add_title_slide(slide_data)
                elif slide_type == 'chart':
                    self._add_chart_slide(slide_data)
                else:
                    self._add_content_slide(slide_data)
            
            self.prs.save(output_path)
            return output_path
            
        except Exception as e:
            print(f"PPT generation failed: {e}")
            raise
    
    def _add_title_slide(self, slide_data: Dict[str, Any]):
        """Add title slide."""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])  # Blank
        
        # Add title
        title_box = slide.shapes.add_textbox(
            Inches(1), Inches(2.5), Inches(8), Inches(1)
        )
        title_frame = title_box.text_frame
        title_frame.text = slide_data.get('title', '')
        
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(44)
        title_para.font.bold = True
        title_para.font.color.rgb = self.colors['primary']
        title_para.alignment = PP_ALIGN.CENTER
        
        # Add subtitle
        if slide_data.get('subtitle'):
            subtitle_box = slide.shapes.add_textbox(
                Inches(1), Inches(3.5), Inches(8), Inches(1)
            )
            subtitle_frame = subtitle_box.text_frame
            subtitle_frame.text = slide_data['subtitle']
            
            sub_para = subtitle_frame.paragraphs[0]
            sub_para.font.size = Pt(24)
            sub_para.font.color.rgb = self.colors['text']
            sub_para.alignment = PP_ALIGN.CENTER
    
    def _add_content_slide(self, slide_data: Dict[str, Any]):
        """Add content slide with bullets."""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])  # Blank
        
        # Title
        title_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(0.3), Inches(9), Inches(0.6)
        )
        title_frame = title_box.text_frame
        title_frame.text = slide_data.get('title', '')
        
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(32)
        title_para.font.bold = True
        title_para.font.color.rgb = self.colors['primary']
        
        # Content
        content_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(1.2), Inches(9), Inches(5.5)
        )
        text_frame = content_box.text_frame
        text_frame.word_wrap = True
        
        for item in slide_data.get('content', []):
            if isinstance(item, str) and item.strip():
                # Clean up formatting
                clean_item = item.replace('•', '').strip()
                clean_item = clean_item.replace('**', '')  # Remove bold markers
                
                p = text_frame.add_paragraph()
                p.text = clean_item
                p.level = 0
                p.font.size = Pt(16)
                p.font.color.rgb = self.colors['text']
                p.space_after = Pt(12)
        
        # Add speaker notes
        if slide_data.get('speaker_notes'):
            notes_slide = slide.notes_slide
            notes_slide.notes_text_frame.text = slide_data['speaker_notes']
    
    def _add_chart_slide(self, slide_data: Dict[str, Any]):
        """Add slide with chart."""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])  # Blank
        
        # Title
        title_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(0.3), Inches(9), Inches(0.6)
        )
        title_frame = title_box.text_frame
        title_frame.text = slide_data.get('title', '')
        
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(28)
        title_para.font.bold = True
        title_para.font.color.rgb = self.colors['primary']
        
        # Chart (convert Plotly to image and insert)
        chart_data = slide_data.get('chart_data')
        if chart_data:
            chart_img = self._plotly_to_bytes(chart_data)
            if chart_img:
                slide.shapes.add_picture(
                    chart_img,
                    Inches(0.5),
                    Inches(1.2),
                    width=Inches(6),
                    height=Inches(4.5)
                )
        
        # Content bullets (on the right side)
        content_box = slide.shapes.add_textbox(
            Inches(6.8), Inches(1.5), Inches(3), Inches(5)
        )
        text_frame = content_box.text_frame
        text_frame.word_wrap = True
        
        for item in slide_data.get('content', []):
            if isinstance(item, str) and item.strip():
                clean_item = item.replace('•', '').strip()
                clean_item = clean_item.replace('**', '')
                
                p = text_frame.add_paragraph()
                p.text = clean_item
                p.font.size = Pt(12)
                p.font.color.rgb = self.colors['text']
                p.space_after = Pt(8)
        
        # Add speaker notes
        if slide_data.get('speaker_notes'):
            notes_slide = slide.notes_slide
            notes_slide.notes_text_frame.text = slide_data['speaker_notes']
    
    def _plotly_to_bytes(self, chart_data: Dict) -> BytesIO:
        """Convert Plotly chart to image bytes."""
        try:
            fig = go.Figure(chart_data)
            img_bytes = fig.to_image(format="png", width=900, height=675)
            return BytesIO(img_bytes)
        except Exception as e:
            print(f"Chart conversion failed: {e}")
            return None
