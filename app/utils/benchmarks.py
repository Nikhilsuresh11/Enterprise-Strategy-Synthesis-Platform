"""Industry benchmark and data validation utilities."""

import json
import os
from typing import Dict, Optional, Any
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Load industry benchmarks
BENCHMARKS_PATH = Path(__file__).parent.parent / "data" / "industry_benchmarks.json"
_benchmarks_cache = None


def load_benchmarks() -> Dict:
    """Load industry benchmarks from JSON file."""
    global _benchmarks_cache
    
    if _benchmarks_cache is not None:
        return _benchmarks_cache
    
    try:
        with open(BENCHMARKS_PATH, 'r') as f:
            _benchmarks_cache = json.load(f)
            logger.info("industry_benchmarks_loaded", path=str(BENCHMARKS_PATH))
            return _benchmarks_cache
    except Exception as e:
        logger.error("failed_to_load_benchmarks", error=str(e))
        # Return minimal defaults
        return {
            "industries": {},
            "regions": {},
            "financial_defaults": {
                "wacc": 0.10,
                "terminal_growth_rate": 0.03
            }
        }


def get_industry_benchmark(industry: str, metric: str, default: Any = None) -> Any:
    """
    Get benchmark value for an industry.
    
    Args:
        industry: Industry name (e.g., "automotive", "technology")
        metric: Metric name (e.g., "cac", "ltv", "gross_margin")
        default: Default value if not found
        
    Returns:
        Benchmark value or default
    """
    benchmarks = load_benchmarks()
    
    # Normalize industry name
    industry_lower = industry.lower().replace(" ", "_").replace("&", "and")
    
    # Try exact match first
    if industry_lower in benchmarks.get("industries", {}):
        return benchmarks["industries"][industry_lower].get(metric, default)
    
    # Try partial matches
    for key in benchmarks.get("industries", {}).keys():
        if industry_lower in key or key in industry_lower:
            return benchmarks["industries"][key].get(metric, default)
    
    # Return default
    logger.warning(
        "industry_benchmark_not_found",
        industry=industry,
        metric=metric,
        using_default=default
    )
    return default


def estimate_cac(industry: str, region: str = "global") -> float:
    """
    Estimate Customer Acquisition Cost based on industry.
    
    Args:
        industry: Industry name
        region: Geographic region
        
    Returns:
        Estimated CAC in USD
    """
    base_cac = get_industry_benchmark(industry, "cac", 500)
    
    # Adjust for region
    if region.lower() in ["india", "china"]:
        base_cac *= 0.6
    
    return float(base_cac)


def estimate_ltv(industry: str, region: str = "global") -> float:
    """
    Estimate Lifetime Value based on industry.
    
    Args:
        industry: Industry name
        region: Geographic region
        
    Returns:
        Estimated LTV in USD
    """
    base_ltv = get_industry_benchmark(industry, "ltv", 2500)
    
    # Adjust for region
    if region.lower() in ["india", "china"]:
        base_ltv *= 0.7
    
    return float(base_ltv)


def estimate_tam(
    industry: str,
    region: str,
    population_millions: Optional[float] = None
) -> float:
    """
    Estimate Total Addressable Market.
    
    Args:
        industry: Industry name
        region: Geographic region
        population_millions: Population in millions
        
    Returns:
        Estimated TAM in USD
    """
    benchmarks = load_benchmarks()
    
    # Get region data
    region_data = benchmarks.get("regions", {}).get(region.lower(), {})
    if not region_data:
        logger.warning("region_not_found", region=region)
        return 1_000_000_000  # Default 1B
    
    pop = population_millions or region_data.get("population_millions", 100)
    avg_income = region_data.get("avg_income_usd", 10000)
    internet_pen = region_data.get("internet_penetration", 0.5)
    
    # Industry multiplier
    multiplier = get_industry_benchmark(industry, "typical_tam_multiplier", 1.0)
    
    # Simple TAM estimation: population * income * penetration * industry factor
    tam = pop * 1_000_000 * (avg_income / 1000) * internet_pen * multiplier * 0.01
    
    return float(tam)


def validate_financial_data(data: Dict, context: str = "") -> Dict:
    """
    Validate and clean financial data with fallbacks.
    
    Args:
        data: Financial data dictionary
        context: Context for logging (e.g., "unit_economics")
        
    Returns:
        Validated and cleaned data dictionary
    """
    validated = {}
    issues = []
    
    for key, value in data.items():
        if value is None or value == 0:
            issues.append(f"{key}=0")
            validated[key] = 0
        elif isinstance(value, (int, float)):
            # Clean floating point artifacts
            validated[key] = round(float(value), 2)
        else:
            validated[key] = value
    
    if issues:
        logger.warning(
            "financial_data_validation_issues",
            context=context,
            issues=issues
        )
    
    return validated


def apply_industry_fallbacks(
    data: Dict,
    industry: str,
    region: str = "global"
) -> Dict:
    """
    Apply industry benchmark fallbacks for missing data.
    
    Args:
        data: Data dictionary with potential missing values
        industry: Industry name
        region: Geographic region
        
    Returns:
        Data with fallbacks applied
    """
    result = data.copy()
    
    # CAC fallback
    if not result.get("cac") or result.get("cac") == 0:
        result["cac"] = estimate_cac(industry, region)
        logger.info("applied_cac_fallback", industry=industry, cac=result["cac"])
    
    # LTV fallback
    if not result.get("ltv") or result.get("ltv") == 0:
        result["ltv"] = estimate_ltv(industry, region)
        logger.info("applied_ltv_fallback", industry=industry, ltv=result["ltv"])
    
    # TAM fallback
    if not result.get("tam") or result.get("tam") == 0:
        result["tam"] = estimate_tam(industry, region)
        logger.info("applied_tam_fallback", industry=industry, tam=result["tam"])
    
    # Gross margin fallback
    if not result.get("gross_margin") or result.get("gross_margin") == 0:
        result["gross_margin"] = get_industry_benchmark(industry, "gross_margin", 0.30)
    
    return result
