"""Regulatory data service - simulated data sources."""

import asyncio
from typing import Dict, Optional, List
from datetime import datetime


class RegulatoryDataService:
    """
    Fetch regulatory data from various sources.
    Currently simulated - replace with real APIs in production.
    
    Real sources to integrate:
    - World Bank Governance Indicators
    - UNCTAD FDI Database
    - WTO Tariff Database
    - ILO Labor Standards
    - Government regulatory portals
    """
    
    def __init__(self):
        """Initialize regulatory data service."""
        pass
    
    async def get_fdi_policy(self, country: str, sector: str) -> Dict:
        """
        Fetch FDI (Foreign Direct Investment) policy.
        
        Args:
            country: Target country
            sector: Industry sector
            
        Returns:
            FDI policy details
        """
        await asyncio.sleep(0.2)  # Simulate API call
        
        # Simulated FDI policies by country
        fdi_policies = {
            "Saudi Arabia": {
                "food_delivery": {
                    "allowed": True,
                    "ownership_limit": 100,
                    "conditions": [
                        "Approval from Ministry of Investment required",
                        "Minimum capital requirement: SAR 5M (~$1.3M)",
                        "Must comply with Saudi Food & Drug Authority regulations"
                    ],
                    "approval_required": True,
                    "timeline_months": 6
                },
                "default": {
                    "allowed": True,
                    "ownership_limit": 49,
                    "conditions": ["Joint venture with local partner required"],
                    "approval_required": True,
                    "timeline_months": 9
                }
            },
            "UAE": {
                "default": {
                    "allowed": True,
                    "ownership_limit": 100,
                    "conditions": ["Commercial license required"],
                    "approval_required": False,
                    "timeline_months": 3
                }
            },
            "India": {
                "default": {
                    "allowed": True,
                    "ownership_limit": 100,
                    "conditions": ["Automatic route for most sectors"],
                    "approval_required": False,
                    "timeline_months": 2
                }
            }
        }
        
        country_policy = fdi_policies.get(country, {})
        sector_key = sector.lower().replace(" ", "_").replace("-", "_")
        policy = country_policy.get(sector_key, country_policy.get("default", {
            "allowed": True,
            "ownership_limit": 100,
            "conditions": [],
            "approval_required": False,
            "timeline_months": 6
        }))
        
        return {
            "country": country,
            "sector": sector,
            **policy,
            "source": "Government FDI Portal (Simulated)",
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
    
    async def get_tax_rates(self, country: str) -> Dict:
        """
        Fetch corporate tax information.
        
        Args:
            country: Target country
            
        Returns:
            Tax rates and treaty information
        """
        await asyncio.sleep(0.2)
        
        tax_data = {
            "Saudi Arabia": {
                "corporate_tax_rate": 0.20,
                "vat_rate": 0.15,
                "withholding_tax": 0.05,
                "tax_treaties": ["India", "UAE", "USA", "UK", "Singapore"],
                "incentives": ["SEZ tax holidays", "R&D tax credits"]
            },
            "UAE": {
                "corporate_tax_rate": 0.09,
                "vat_rate": 0.05,
                "withholding_tax": 0.00,
                "tax_treaties": ["India", "Saudi Arabia", "USA", "UK"],
                "incentives": ["Free zone 0% tax", "No personal income tax"]
            },
            "India": {
                "corporate_tax_rate": 0.25,
                "vat_rate": 0.18,  # GST
                "withholding_tax": 0.10,
                "tax_treaties": ["UAE", "Saudi Arabia", "USA", "UK", "Singapore"],
                "incentives": ["Startup tax exemption", "SEZ benefits"]
            }
        }
        
        data = tax_data.get(country, {
            "corporate_tax_rate": 0.25,
            "vat_rate": 0.15,
            "withholding_tax": 0.10,
            "tax_treaties": [],
            "incentives": []
        })
        
        return {
            "country": country,
            **data,
            "source": "KPMG Global Tax Database (Simulated)"
        }
    
    async def get_political_risk_score(self, country: str) -> Dict:
        """
        Get political risk and stability metrics.
        
        Args:
            country: Target country
            
        Returns:
            Political risk scores
        """
        await asyncio.sleep(0.2)
        
        risk_scores = {
            "Saudi Arabia": {
                "stability_index": 7.5,
                "government_effectiveness": 7.0,
                "regulatory_quality": 7.2,
                "rule_of_law": 6.8,
                "corruption_perception": 6.5,
                "risk_level": "medium"
            },
            "UAE": {
                "stability_index": 8.5,
                "government_effectiveness": 8.2,
                "regulatory_quality": 8.0,
                "rule_of_law": 7.5,
                "corruption_perception": 7.8,
                "risk_level": "low"
            },
            "India": {
                "stability_index": 6.5,
                "government_effectiveness": 6.0,
                "regulatory_quality": 6.2,
                "rule_of_law": 5.8,
                "corruption_perception": 5.5,
                "risk_level": "medium"
            }
        }
        
        scores = risk_scores.get(country, {
            "stability_index": 5.0,
            "government_effectiveness": 5.0,
            "regulatory_quality": 5.0,
            "rule_of_law": 5.0,
            "corruption_perception": 5.0,
            "risk_level": "high"
        })
        
        return {
            "country": country,
            **scores,
            "source": "World Bank Governance Indicators (Simulated)"
        }
    
    async def get_trade_data(
        self,
        export_country: str,
        import_country: str,
        hs_code: Optional[str] = None
    ) -> Dict:
        """
        Fetch tariff and trade barrier information.
        
        Args:
            export_country: Exporting country
            import_country: Importing country
            hs_code: Optional HS code for specific product
            
        Returns:
            Trade data including tariffs
        """
        await asyncio.sleep(0.2)
        
        # Check for trade agreements
        trade_agreements = {
            ("India", "UAE"): {"name": "India-UAE CEPA", "tariff_rate": 0.00},
            ("India", "Saudi Arabia"): {"name": "GCC-India FTA (under negotiation)", "tariff_rate": 0.05},
            ("UAE", "Saudi Arabia"): {"name": "GCC Common Market", "tariff_rate": 0.00}
        }
        
        route = (export_country, import_country)
        agreement = trade_agreements.get(route, None)
        
        if agreement:
            return {
                "route": f"{export_country} → {import_country}",
                "tariff_rate": agreement["tariff_rate"],
                "free_trade_agreement": True,
                "agreement_name": agreement["name"],
                "quotas": [],
                "import_restrictions": [],
                "source": "WTO Tariff Database (Simulated)"
            }
        else:
            return {
                "route": f"{export_country} → {import_country}",
                "tariff_rate": 0.10,
                "free_trade_agreement": False,
                "agreement_name": None,
                "quotas": [],
                "import_restrictions": ["Standard customs clearance required"],
                "source": "WTO Tariff Database (Simulated)"
            }
    
    async def get_labor_laws(self, country: str) -> Dict:
        """
        Fetch labor regulation summary.
        
        Args:
            country: Target country
            
        Returns:
            Labor law details
        """
        await asyncio.sleep(0.2)
        
        labor_data = {
            "Saudi Arabia": {
                "min_wage_usd_monthly": 800,
                "standard_hours_per_week": 48,
                "overtime_premium": 1.5,
                "paid_leave_days": 21,
                "maternity_leave_weeks": 10,
                "local_hiring_requirement": 0.75,  # Saudization
                "union_presence": "low"
            },
            "UAE": {
                "min_wage_usd_monthly": 0,  # No official minimum wage
                "standard_hours_per_week": 48,
                "overtime_premium": 1.25,
                "paid_leave_days": 30,
                "maternity_leave_weeks": 8,
                "local_hiring_requirement": 0.02,  # Emiratization (varies by sector)
                "union_presence": "low"
            },
            "India": {
                "min_wage_usd_monthly": 200,  # Varies by state
                "standard_hours_per_week": 48,
                "overtime_premium": 2.0,
                "paid_leave_days": 12,
                "maternity_leave_weeks": 26,
                "local_hiring_requirement": 0.00,  # No formal requirement
                "union_presence": "medium"
            }
        }
        
        data = labor_data.get(country, {
            "min_wage_usd_monthly": 500,
            "standard_hours_per_week": 40,
            "overtime_premium": 1.5,
            "paid_leave_days": 15,
            "maternity_leave_weeks": 12,
            "local_hiring_requirement": 0.50,
            "union_presence": "medium"
        })
        
        return {
            "country": country,
            **data,
            "source": "ILO Database (Simulated)"
        }
