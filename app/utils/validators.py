"""Input validation utilities."""

import re
from typing import Optional


def validate_company_name(name: str) -> bool:
    """
    Validate company name format.
    
    Args:
        name: Company name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name or len(name.strip()) < 2:
        return False
    # Allow letters, numbers, spaces, and common business characters
    pattern = r'^[a-zA-Z0-9\s\.\,\&\-\_]+$'
    return bool(re.match(pattern, name))


def validate_industry(industry: str) -> bool:
    """
    Validate industry format.
    
    Args:
        industry: Industry to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not industry or len(industry.strip()) < 2:
        return False
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and invalid characters.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove path separators and invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    # Limit length
    return sanitized[:255]


def validate_job_id(job_id: str) -> bool:
    """
    Validate job ID format (UUID).
    
    Args:
        job_id: Job ID to validate
        
    Returns:
        True if valid UUID format, False otherwise
    """
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, job_id.lower()))
