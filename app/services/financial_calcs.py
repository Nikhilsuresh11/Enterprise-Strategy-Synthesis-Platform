"""Financial calculation functions for analyst agent."""

import numpy as np
from typing import List, Dict, Tuple, Optional


def calculate_tam(
    total_population: float,
    addressable_percentage: float,
    avg_spending_per_capita: float
) -> float:
    """
    Calculate Total Addressable Market.
    
    Args:
        total_population: Total population in target market
        addressable_percentage: % of population that could use product (0.0-1.0)
        avg_spending_per_capita: Average annual spending per person
        
    Returns:
        TAM in currency units
    """
    return total_population * addressable_percentage * avg_spending_per_capita


def calculate_sam(
    tam: float,
    target_segment_percentage: float
) -> float:
    """
    Calculate Serviceable Addressable Market.
    
    Args:
        tam: Total Addressable Market
        target_segment_percentage: % of TAM actually targetable (0.0-1.0)
        
    Returns:
        SAM in currency units
    """
    return tam * target_segment_percentage


def calculate_som(
    sam: float,
    realistic_market_share: float,
    years_to_achieve: int = 5
) -> Dict[str, any]:
    """
    Calculate Serviceable Obtainable Market with S-curve adoption.
    
    Args:
        sam: Serviceable Addressable Market
        realistic_market_share: Target market share (0.0-1.0)
        years_to_achieve: Years to reach target share
        
    Returns:
        Dictionary with final SOM and yearly progression
    """
    final_som = sam * realistic_market_share
    
    # S-curve (logistic) adoption model
    yearly_som = []
    for year in range(1, years_to_achieve + 1):
        progress = year / years_to_achieve
        # Logistic growth: slow start, rapid middle, slow end
        share_achieved = 1 / (1 + np.exp(-10 * (progress - 0.5)))
        yearly_som.append(final_som * share_achieved)
    
    return {
        "final_som": final_som,
        "yearly_progression": yearly_som,
        "market_share_target": realistic_market_share,
        "years": years_to_achieve
    }


def calculate_ltv(
    avg_revenue_per_customer: float,
    gross_margin: float,
    retention_rate: float,
    discount_rate: float = 0.10
) -> float:
    """
    Calculate Customer Lifetime Value.
    
    Args:
        avg_revenue_per_customer: Average monthly/annual revenue per customer
        gross_margin: Gross margin percentage (0.0-1.0)
        retention_rate: Monthly/annual retention rate (0.0-1.0)
        discount_rate: Discount rate for NPV (0.0-1.0)
        
    Returns:
        LTV in currency units
    """
    margin_per_customer = avg_revenue_per_customer * gross_margin
    
    # Geometric series for infinite time horizon
    # LTV = Margin / (1 + discount_rate - retention_rate)
    ltv = margin_per_customer / (1 + discount_rate - retention_rate)
    
    return ltv


def calculate_cac(
    total_marketing_spend: float,
    total_sales_spend: float,
    new_customers_acquired: int
) -> float:
    """
    Calculate Customer Acquisition Cost.
    
    Args:
        total_marketing_spend: Total marketing expenses
        total_sales_spend: Total sales expenses
        new_customers_acquired: Number of new customers
        
    Returns:
        CAC per customer
    """
    if new_customers_acquired == 0:
        return 0.0
    
    return (total_marketing_spend + total_sales_spend) / new_customers_acquired


def calculate_wacc(
    cost_of_equity: float,
    cost_of_debt: float,
    equity_weight: float,
    debt_weight: float,
    tax_rate: float
) -> float:
    """
    Calculate Weighted Average Cost of Capital.
    
    Args:
        cost_of_equity: Cost of equity (0.0-1.0)
        cost_of_debt: Cost of debt (0.0-1.0)
        equity_weight: Weight of equity in capital structure (0.0-1.0)
        debt_weight: Weight of debt in capital structure (0.0-1.0)
        tax_rate: Corporate tax rate (0.0-1.0)
        
    Returns:
        WACC as decimal
    """
    return (equity_weight * cost_of_equity) + \
           (debt_weight * cost_of_debt * (1 - tax_rate))


def dcf_valuation(
    cash_flows: List[float],
    discount_rate: float,
    terminal_growth_rate: float
) -> Dict[str, float]:
    """
    Discounted Cash Flow valuation with terminal value.
    
    Args:
        cash_flows: List of projected free cash flows
        discount_rate: WACC or discount rate (0.0-1.0)
        terminal_growth_rate: Perpetual growth rate (0.0-1.0)
        
    Returns:
        Dictionary with valuation components
    """
    # Discount projected cash flows to present value
    pv_cash_flows = []
    for i, cf in enumerate(cash_flows, start=1):
        pv = cf / ((1 + discount_rate) ** i)
        pv_cash_flows.append(pv)
    
    # Terminal value using Gordon Growth Model
    final_cf = cash_flows[-1]
    terminal_value = (final_cf * (1 + terminal_growth_rate)) / \
                     (discount_rate - terminal_growth_rate)
    
    # Discount terminal value to present
    pv_terminal = terminal_value / ((1 + discount_rate) ** len(cash_flows))
    
    # Enterprise value = sum of discounted CFs + discounted terminal value
    enterprise_value = sum(pv_cash_flows) + pv_terminal
    
    return {
        "pv_cash_flows": pv_cash_flows,
        "sum_pv_cash_flows": sum(pv_cash_flows),
        "terminal_value": terminal_value,
        "pv_terminal": pv_terminal,
        "enterprise_value": enterprise_value,
        "assumptions": {
            "discount_rate": discount_rate,
            "terminal_growth_rate": terminal_growth_rate,
            "projection_years": len(cash_flows)
        }
    }


def sensitivity_analysis(
    base_value: float,
    variable_name: str,
    variable_range: List[float],
    calc_function: callable
) -> Dict[str, any]:
    """
    Run sensitivity analysis on a variable.
    
    Args:
        base_value: Base case output value
        variable_name: Name of variable being tested
        variable_range: List of values to test
        calc_function: Function that takes variable value and returns output
        
    Returns:
        Sensitivity table with impacts
    """
    results = []
    for value in variable_range:
        try:
            result = calc_function(value)
            impact = ((result - base_value) / base_value) * 100 if base_value != 0 else 0
            results.append({
                "variable_value": value,
                "output": result,
                "impact_pct": impact
            })
        except Exception as e:
            results.append({
                "variable_value": value,
                "output": None,
                "impact_pct": None,
                "error": str(e)
            })
    
    return {
        "variable": variable_name,
        "base_value": base_value,
        "sensitivity_table": results
    }


def calculate_payback_period(
    cac: float,
    monthly_revenue: float,
    gross_margin: float
) -> float:
    """
    Calculate payback period in months.
    
    Args:
        cac: Customer Acquisition Cost
        monthly_revenue: Average monthly revenue per customer
        gross_margin: Gross margin percentage (0.0-1.0)
        
    Returns:
        Payback period in months
    """
    monthly_margin = monthly_revenue * gross_margin
    
    if monthly_margin == 0:
        return float('inf')
    
    return cac / monthly_margin


def calculate_contribution_margin(
    revenue: float,
    variable_costs: float
) -> Dict[str, float]:
    """
    Calculate contribution margin.
    
    Args:
        revenue: Total revenue
        variable_costs: Total variable costs
        
    Returns:
        Contribution margin amount and percentage
    """
    margin_amount = revenue - variable_costs
    margin_pct = (margin_amount / revenue) if revenue > 0 else 0
    
    return {
        "margin_amount": margin_amount,
        "margin_percentage": margin_pct
    }
