"""Deck generation service - unified PDF/PPT/JSON output."""

import os
import json
from typing import List, Dict, Any
from datetime import datetime

from app.services.pdf_generator import PDFGenerator
from app.services.ppt_generator import PPTGenerator


class DeckGenerationService:
    """Service for generating all output formats (PDF, PPT, JSON)."""
    
    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize deck generation service.
        
        Args:
            output_dir: Directory to save generated files
        """
        self.output_dir = output_dir
        self.pdf_gen = PDFGenerator()
        self.ppt_gen = PPTGenerator()
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def generate_all_outputs(
        self,
        job_id: str,
        slides: List[Dict[str, Any]],
        synthesis: Dict[str, Any],
        company_name: str
    ) -> Dict[str, str]:
        """
        Generate PDF, PPT, and JSON outputs.
        
        Args:
            job_id: Unique job identifier
            slides: List of slide dictionaries
            synthesis: Synthesis data
            company_name: Company name
            
        Returns:
            Dictionary with file paths for each format
        """
        try:
            # Create base filename
            safe_company = company_name.replace(' ', '_').replace('/', '_')
            base_filename = f"{job_id}_{safe_company}"
            
            output_paths = {}
            
            # Generate PDF
            pdf_path = os.path.join(self.output_dir, f"{base_filename}.pdf")
            await self.pdf_gen.generate_pdf(slides, pdf_path, company_name)
            output_paths['pdf'] = pdf_path
            
            # Generate PPT
            ppt_path = os.path.join(self.output_dir, f"{base_filename}.pptx")
            await self.ppt_gen.generate_ppt(slides, ppt_path)
            output_paths['pptx'] = ppt_path
            
            # Generate JSON
            json_path = os.path.join(self.output_dir, f"{base_filename}.json")
            json_data = {
                "job_id": job_id,
                "company": company_name,
                "slides": slides,
                "synthesis": synthesis,
                "generated_at": datetime.now().isoformat()
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            output_paths['json'] = json_path
            
            return output_paths
            
        except Exception as e:
            print(f"Deck generation failed: {e}")
            raise
