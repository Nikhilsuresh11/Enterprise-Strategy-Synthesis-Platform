"""Number formatting utilities for financial and business metrics."""

from typing import Optional, Union


def format_currency(
    amount: Optional[Union[float, int]],
    currency: str = "USD",
    decimals: int = 2
) -> str:
    """
    Format a number as currency with proper rounding.
    
    Args:
        amount: Amount to format
        currency: Currency code (default: USD)
        decimals: Number of decimal places
        
    Returns:
        Formatted currency string
    """
    if amount is None or amount == 0:
        return f"${0:.{decimals}f}"
    
    # Round to avoid floating point artifacts
    amount = round(float(amount), decimals)
    
    # Format with commas
    if abs(amount) >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.{decimals}f}B"
    elif abs(amount) >= 1_000_000:
        return f"${amount / 1_000_000:.{decimals}f}M"
    elif abs(amount) >= 1_000:
        return f"${amount / 1_000:.{decimals}f}K"
    else:
        return f"${amount:,.{decimals}f}"


def format_percentage(
    value: Optional[Union[float, int]],
    decimals: int = 1
) -> str:
    """
    Format a number as a percentage.
    
    Args:
        value: Value to format (0.15 = 15%)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    if value is None:
        return "0.0%"
    
    value = round(float(value) * 100, decimals)
    return f"{value:.{decimals}f}%"


def format_ratio(
    numerator: Optional[Union[float, int]],
    denominator: Optional[Union[float, int]],
    decimals: int = 1,
    suffix: str = "x"
) -> str:
    """
    Format a ratio with validation.
    
    Args:
        numerator: Top of ratio
        denominator: Bottom of ratio
        decimals: Number of decimal places
        suffix: Suffix to add (default: 'x')
        
    Returns:
        Formatted ratio string
    """
    if not numerator or not denominator or denominator == 0:
        return f"0.0{suffix}"
    
    ratio = round(float(numerator) / float(denominator), decimals)
    return f"{ratio:.{decimals}f}{suffix}"


def format_number(
    value: Optional[Union[float, int]],
    decimals: int = 2,
    use_abbreviation: bool = True
) -> str:
    """
    Format a number with proper rounding and abbreviation.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        use_abbreviation: Use K/M/B abbreviations
        
    Returns:
        Formatted number string
    """
    if value is None or value == 0:
        return "0"
    
    value = round(float(value), decimals)
    
    if not use_abbreviation:
        return f"{value:,.{decimals}f}"
    
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.{decimals}f}B"
    elif abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.{decimals}f}M"
    elif abs(value) >= 1_000:
        return f"{value / 1_000:.{decimals}f}K"
    else:
        return f"{value:.{decimals}f}"


def safe_divide(
    numerator: Optional[Union[float, int]],
    denominator: Optional[Union[float, int]],
    default: float = 0.0
) -> float:
    """
    Safely divide two numbers with validation.
    
    Args:
        numerator: Top of division
        denominator: Bottom of division
        default: Default value if division fails
        
    Returns:
        Result of division or default
    """
    try:
        if not denominator or denominator == 0:
            return default
        return float(numerator) / float(denominator)
    except (TypeError, ValueError, ZeroDivisionError):
        return default


def clean_float(value: any, default: float = 0.0) -> float:
    """
    Clean and convert a value to float.
    
    Args:
        value: Value to convert
        default: Default if conversion fails
        
    Returns:
        Cleaned float value
    """
    if value is None:
        return default
    
    try:
        # Handle string inputs
        if isinstance(value, str):
            # Remove currency symbols and commas
            value = value.replace('$', '').replace(',', '').replace('%', '')
            # Remove B/M/K suffixes
            multiplier = 1
            if value.endswith('B'):
                multiplier = 1_000_000_000
                value = value[:-1]
            elif value.endswith('M'):
                multiplier = 1_000_000
                value = value[:-1]
            elif value.endswith('K'):
                multiplier = 1_000
                value = value[:-1]
            
            return float(value) * multiplier
        
        return float(value)
    except (TypeError, ValueError):
        return default
