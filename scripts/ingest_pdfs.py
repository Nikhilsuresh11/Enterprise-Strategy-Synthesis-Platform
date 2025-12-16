"""
PDF Document Ingestion Script

Processes PDF files and ingests them into Pinecone.
Useful for case studies, reports, and regulatory documents.

Usage:
    python scripts/ingest_pdfs.py --directory data/pdfs
    python scripts/ingest_pdfs.py --file document.pdf
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import PyPDF2
from typing import List, Dict
import hashlib

from app.services.rag_service import RAGService
from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PDFIngester:
    """Ingest PDF documents into Pinecone."""
    
    def __init__(self):
        """Initialize PDF ingester."""
        self.settings = get_settings()
        self.rag_service = None
    
    async def initialize(self):
        """Initialize RAG service."""
        self.rag_service = RAGService(
            api_key=self.settings.pinecone_api_key,
            environment=self.settings.pinecone_environment,
            index_name=self.settings.pinecone_index_name
        )
        await self.rag_service.connect()
        logger.info("RAG service initialized")
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            return ""
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                if last_period > chunk_size * 0.7:  # At least 70% through
                    end = start + last_period + 1
                    chunk = text[start:end]
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    async def ingest_pdf(self, pdf_path: Path, category: str = "general"):
        """Ingest single PDF file."""
        logger.info(f"Processing: {pdf_path.name}")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text or len(text) < 100:
            logger.warning(f"Insufficient text extracted from {pdf_path.name}")
            return 0
        
        # Create chunks
        chunks = self.chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks from {pdf_path.name}")
        
        # Ingest each chunk
        for i, chunk in enumerate(chunks):
            try:
                # Create unique ID
                doc_id = hashlib.md5(f"{pdf_path.name}_{i}".encode()).hexdigest()
                
                metadata = {
                    "source": pdf_path.stem,
                    "filename": pdf_path.name,
                    "category": category,
                    "chunk": i,
                    "total_chunks": len(chunks),
                    "file_type": "pdf"
                }
                
                await self.rag_service.ingest_document(
                    text=chunk,
                    metadata=metadata
                )
                
            except Exception as e:
                logger.error(f"Failed to ingest chunk {i} from {pdf_path.name}: {e}")
                continue
        
        logger.info(f"✓ Ingested {pdf_path.name} ({len(chunks)} chunks)")
        return len(chunks)
    
    async def ingest_directory(self, directory: Path, category: str = "general"):
        """Ingest all PDFs from directory."""
        pdf_files = list(directory.glob("**/*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        total_chunks = 0
        for pdf_file in pdf_files:
            chunks = await self.ingest_pdf(pdf_file, category)
            total_chunks += chunks
        
        logger.info(f"Total: {total_chunks} chunks from {len(pdf_files)} files")


async def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest PDF documents")
    parser.add_argument("--directory", type=str, help="Directory containing PDFs")
    parser.add_argument("--file", type=str, help="Single PDF file to ingest")
    parser.add_argument("--category", type=str, default="general", help="Document category")
    
    args = parser.parse_args()
    
    if not args.directory and not args.file:
        print("Error: Specify --directory or --file")
        return
    
    print("\n" + "="*80)
    print("PDF INGESTION TO PINECONE")
    print("="*80 + "\n")
    
    ingester = PDFIngester()
    await ingester.initialize()
    
    if args.file:
        pdf_path = Path(args.file)
        if pdf_path.exists():
            await ingester.ingest_pdf(pdf_path, args.category)
        else:
            print(f"Error: File not found: {args.file}")
    
    if args.directory:
        dir_path = Path(args.directory)
        if dir_path.exists():
            await ingester.ingest_directory(dir_path, args.category)
        else:
            print(f"Error: Directory not found: {args.directory}")
    
    print("\n" + "="*80)
    print("INGESTION COMPLETE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
