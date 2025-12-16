"""Prompt templates for Analyst Agent."""

TAM_SAM_SOM_PROMPT = """
You are a senior financial analyst at McKinsey & Company calculating market size.

===== COMPANY & INDUSTRY =====
Company: {company}
Industry: {industry}
Region: {region}

===== MARKET DATA FROM RESEARCH =====
{market_data}

===== RESEARCH CONTEXT =====
{research_context}

===== TASK =====
Calculate TAM, SAM, and SOM using rigorous methodology:

**1. TAM (Total Addressable Market)**
- Use top-down approach: Total market size from industry reports
- Use bottom-up approach: Population × adoption rate × ARPU
- Choose most reliable method and explain why

**2. SAM (Serviceable Addressable Market)**
- Apply geographic constraints (which regions are actually targetable)
- Apply regulatory constraints (where can we legally operate)
- Apply target customer segment filters

**3. SOM (Serviceable Obtainable Market)**
- Realistic market share achievable in Year 1 and Year 5
- Consider competitive landscape and barriers to entry
- Account for brand strength and go-to-market strategy

**IMPORTANT**:
- Base calculations ONLY on provided data
- State all assumptions explicitly
- Provide conservative estimates
- Show calculation steps

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "TAM": {{
    "value_usd_millions": float,
    "methodology": "top-down" or "bottom-up",
    "calculation": "Detailed calculation steps",
    "assumptions": ["assumption1", "assumption2"]
  }},
  "SAM": {{
    "value_usd_millions": float,
    "percentage_of_tam": float,
    "constraints": ["constraint1", "constraint2"],
    "assumptions": ["assumption1"]
  }},
  "SOM": {{
    "year_1_usd_millions": float,
    "year_5_usd_millions": float,
    "market_share_year_1": float,
    "market_share_year_5": float,
    "assumptions": ["assumption1", "assumption2"]
  }}
}}
"""

COMPETITIVE_ANALYSIS_PROMPT = """
You are a competitive intelligence analyst at McKinsey & Company.

===== COMPANY =====
{company}

===== INDUSTRY =====
{industry}

===== COMPANY DATA =====
{company_data}

===== COMPETITOR DATA =====
{competitor_data}

===== TASK =====
Analyze {company}'s competitive position:

**1. Competitive Positioning**
- Classify as: Market Leader / Strong Challenger / Niche Player / Emerging Entrant
- Justify classification with data

**2. Key Differentiators**
- What makes {company} unique?
- Sustainable competitive advantages

**3. Competitive Gaps**
- Where do competitors have advantages?
- What capabilities are missing?

**4. Market Share Analysis**
- Estimated current market share
- Trend (gaining/losing share)

**5. Strategic Recommendations**
- How to strengthen position
- Competitive threats to watch

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "positioning": "leader/challenger/niche/emerging",
  "positioning_rationale": "2-3 sentence justification",
  "market_share_estimate": float,
  "key_differentiators": ["diff1", "diff2"],
  "competitive_advantages": ["advantage1", "advantage2"],
  "competitive_gaps": ["gap1", "gap2"],
  "strategic_recommendations": ["rec1", "rec2"]
}}
"""

PORTERS_FIVE_FORCES_PROMPT = """
You are a strategy consultant conducting Porter's Five Forces analysis.

===== INDUSTRY =====
{industry}

===== MARKET CONTEXT =====
{context}

===== COMPETITIVE DATA =====
{competitive_data}

===== TASK =====
Analyze industry attractiveness using Porter's Five Forces framework.

For EACH force, provide:
- **Score**: 1-5 (1=Low intensity/threat, 5=High intensity/threat)
- **Rationale**: 2-3 sentences explaining the score
- **Key Factors**: Specific factors driving the score

**FORCES TO ANALYZE**:

**1. Threat of New Entrants**
- Capital requirements
- Economies of scale
- Brand loyalty
- Regulatory barriers

**2. Bargaining Power of Suppliers**
- Supplier concentration
- Switching costs
- Importance to suppliers

**3. Bargaining Power of Buyers**
- Buyer concentration
- Price sensitivity
- Switching costs

**4. Threat of Substitutes**
- Availability of alternatives
- Price-performance trade-off
- Switching ease

**5. Competitive Rivalry**
- Number of competitors
- Industry growth rate
- Exit barriers
- Product differentiation

**OVERALL ASSESSMENT**:
- Industry attractiveness: High / Medium / Low
- Key insights for strategy

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "forces": {{
    "new_entrants": {{
      "score": int (1-5),
      "rationale": "string",
      "key_factors": ["factor1", "factor2"]
    }},
    "supplier_power": {{...}},
    "buyer_power": {{...}},
    "substitutes": {{...}},
    "rivalry": {{...}}
  }},
  "overall_attractiveness": "high/medium/low",
  "average_score": float,
  "key_insights": ["insight1", "insight2", "insight3"]
}}
"""

SCENARIO_MODELING_PROMPT = """
You are a financial modeler creating scenario analysis.

===== COMPANY & STRATEGY =====
Company: {company}
Strategy: {strategy}

===== BASE MODEL =====
{base_projections}

===== RISK FACTORS =====
{risks}

===== TASK =====
Create THREE scenarios with distinct assumptions:

**1. BASE CASE (50% probability)**
- Realistic, most likely outcome
- Moderate growth assumptions
- Expected market conditions

**2. UPSIDE CASE (25% probability)**
- Optimistic but plausible
- What needs to go RIGHT:
  * Faster market adoption
  * Successful product launches
  * Favorable regulations
  * Strong competitive position

**3. DOWNSIDE CASE (25% probability)**
- Pessimistic but realistic
- What could go WRONG:
  * Slower adoption
  * Competitive pressure
  * Regulatory headwinds
  * Economic downturn

**FOR EACH SCENARIO, ADJUST**:
- Revenue growth rates (Year 1-5)
- Market penetration rates
- Customer acquisition costs
- Gross margins
- Operating expenses

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "base": {{
    "revenue_projections": [year1, year2, year3, year4, year5],
    "growth_rates": [rate1, rate2, rate3, rate4],
    "key_assumptions": ["assumption1", "assumption2"],
    "probability": 0.50
  }},
  "upside": {{
    "revenue_projections": [...],
    "growth_rates": [...],
    "key_assumptions": [...],
    "what_goes_right": ["factor1", "factor2"],
    "probability": 0.25
  }},
  "downside": {{
    "revenue_projections": [...],
    "growth_rates": [...],
    "key_assumptions": [...],
    "what_goes_wrong": ["risk1", "risk2"],
    "probability": 0.25
  }}
}}
"""

UNIT_ECONOMICS_PROMPT = """
You are a financial analyst calculating unit economics.

===== COMPANY =====
{company}

===== BUSINESS MODEL =====
{business_model}

===== FINANCIAL DATA =====
{financial_data}

===== TASK =====
Calculate key unit economics metrics:

**1. CAC (Customer Acquisition Cost)**
- Marketing spend per customer
- Sales spend per customer
- Total CAC

**2. LTV (Lifetime Value)**
- Average revenue per customer
- Gross margin
- Retention rate
- Discounted LTV

**3. LTV/CAC Ratio**
- Target: >3.0 (healthy)
- Interpretation

**4. Payback Period**
- Months to recover CAC
- Target: <12 months

**5. Contribution Margin**
- Per customer
- Per transaction

**BENCHMARKS**:
- Compare to industry standards
- Identify if metrics are healthy

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "CAC": float,
  "LTV": float,
  "LTV_CAC_ratio": float,
  "payback_months": float,
  "contribution_margin_pct": float,
  "assessment": "healthy/concerning/critical",
  "benchmarks": {{
    "industry_avg_ltv_cac": float,
    "industry_avg_payback": float
  }},
  "recommendations": ["rec1", "rec2"]
}}
"""
