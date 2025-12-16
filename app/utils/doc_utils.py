"""Document processing utilities for RAG system."""

from typing import Any, Dict, List
from datetime import datetime

from app.models.schemas import Citation


def extract_citations(text: str, sources: List[Dict[str, Any]]) -> List[Citation]:
    """
    Extract and format citations from retrieved documents.
    
    Args:
        text: Generated text
        sources: List of source documents
        
    Returns:
        List of Citation objects
    """
    citations = []
    
    for source in sources:
        metadata = source.get('metadata', {})
        score = source.get('score', 0.0)
        
        citation = Citation(
            source=metadata.get('source', 'Unknown'),
            url=metadata.get('url'),
            date=metadata.get('date'),
            relevance_score=score
        )
        citations.append(citation)
    
    return citations


def format_rag_context(
    documents: List[Dict[str, Any]],
    max_tokens: int = 3000
) -> str:
    """
    Format RAG results into context string for LLM.
    
    Args:
        documents: Retrieved documents
        max_tokens: Maximum tokens (approximate as chars/4)
        
    Returns:
        Formatted context string
    """
    if not documents:
        return "No relevant context found."
    
    max_chars = max_tokens * 4  # Rough approximation
    context_parts = []
    current_length = 0
    
    for idx, doc in enumerate(documents, 1):
        metadata = doc.get('metadata', {})
        text = doc.get('text', '')
        score = doc.get('score', 0.0)
        
        source = metadata.get('source', 'Unknown')
        date = metadata.get('date', 'N/A')
        source_type = metadata.get('source_type', 'N/A')
        credibility = metadata.get('credibility_score', 0.0)
        
        part = (
            f"\n--- Document {idx} ---\n"
            f"Source: {source} ({source_type})\n"
            f"Date: {date}\n"
            f"Relevance: {score:.2f} | Credibility: {credibility:.2f}\n\n"
            f"{text}\n"
        )
        
        if current_length + len(part) > max_chars:
            break
        
        context_parts.append(part)
        current_length += len(part)
    
    return "".join(context_parts)


def calculate_relevance_score(
    query: str,
    document: Dict[str, Any],
    recency_weight: float = 0.3
) -> float:
    """
    Calculate combined relevance score.
    
    Args:
        query: Search query
        document: Document with metadata
        recency_weight: Weight for recency factor (0.0 to 1.0)
        
    Returns:
        Combined score (0.0 to 1.0)
    """
    # Get base similarity score
    similarity_score = document.get('score', 0.0)
    
    # Calculate recency score
    metadata = document.get('metadata', {})
    date_str = metadata.get('date')
    recency_score = 0.5  # Default
    
    if date_str:
        try:
            doc_date = datetime.fromisoformat(date_str)
            now = datetime.utcnow()
            days_old = (now - doc_date).days
            
            # Exponential decay: newer is better
            recency_score = max(0.0, 1.0 - (days_old / 365.0))
        except:
            pass
    
    # Get credibility score
    credibility_score = metadata.get('credibility_score', 0.5)
    
    # Combine scores
    combined_score = (
        (1.0 - recency_weight) * similarity_score +
        recency_weight * (0.5 * recency_score + 0.5 * credibility_score)
    )
    
    return min(1.0, max(0.0, combined_score))


async def deduplicate_sources(
    documents: List[Dict[str, Any]],
    similarity_threshold: float = 0.95
) -> List[Dict[str, Any]]:
    """
    Remove near-duplicate documents.
    
    Args:
        documents: List of documents
        similarity_threshold: Threshold for considering duplicates
        
    Returns:
        Deduplicated list
    """
    if not documents:
        return []
    
    unique_docs = []
    seen_texts = set()
    
    for doc in documents:
        text = doc.get('text', '').strip()
        
        # Simple deduplication based on text similarity
        # For production, use more sophisticated methods
        text_lower = text.lower()[:200]  # First 200 chars
        
        if text_lower not in seen_texts:
            unique_docs.append(doc)
            seen_texts.add(text_lower)
    
    return unique_docs


def truncate_text(text: str, max_length: int = 500) -> str:
    """
    Truncate text to maximum length with ellipsis.
    
    Args:
        text: Input text
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def validate_research_data(data: Dict) -> tuple[bool, List[str]]:
    """
    Validates research data completeness and quality.
    
    Args:
        data: Research data dictionary
        
    Returns:
        (is_valid, list_of_issues)
    """
    issues = []
    
    required_fields = [
        "key_findings",
        "market_context",
        "competitive_overview",
        "data_quality"
    ]
    
    for field in required_fields:
        if field not in data or not data[field]:
            issues.append(f"Missing required field: {field}")
    
    # Check data freshness
    if "data_quality" in data:
        quality = data["data_quality"]
        if isinstance(quality, dict):
            if quality.get("completeness", 0) < 0.5:
                issues.append("Low data completeness (<50%)")
            if quality.get("reliability", 0) < 0.6:
                issues.append("Low data reliability (<60%)")
    
    return len(issues) == 0, issues


def calculate_research_confidence(data: Dict) -> float:
    """
    Calculate overall confidence score for research.
    
    Based on: completeness, recency, source diversity
    
    Args:
        data: Research data dictionary
        
    Returns:
        Confidence score (0.0-1.0)
    """
    if "data_quality" not in data:
        return 0.5
    
    quality = data["data_quality"]
    
    if not isinstance(quality, dict):
        return 0.5
    
    completeness = quality.get("completeness", 0.5)
    reliability = quality.get("reliability", 0.5)
    source_count = quality.get("source_count", 0)
    
    # Source diversity score (more sources = better)
    diversity_score = min(1.0, source_count / 20.0)
    
    # Weighted average
    confidence = (
        0.4 * completeness +
        0.4 * reliability +
        0.2 * diversity_score
    )
    
    return min(1.0, max(0.0, confidence))
