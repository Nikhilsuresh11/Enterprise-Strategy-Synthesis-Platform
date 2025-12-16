"""Prompt templates for Regulatory Agent."""

FDI_ANALYSIS_PROMPT = """
You are a regulatory expert analyzing FDI (Foreign Direct Investment) regulations.

===== COMPANY =====
{company}

===== SOURCE COUNTRY =====
{source_country}

===== TARGET COUNTRY =====
{target_country}

===== INDUSTRY =====
{industry}

===== FDI POLICY DATA =====
{fdi_policy}

===== CONTEXT =====
{context}

===== TASK =====
Analyze the FDI regulatory environment:

1. **Is FDI permitted** in this sector?
2. **Ownership restrictions**: What percentage can foreign investors own?
3. **Approvals required**: Which government bodies must approve?
4. **Conditions**: What are the key conditions and requirements?
5. **Timeline**: How long does the approval process take?
6. **Key risks**: What regulatory risks exist?

Provide detailed analysis with specific regulations cited.

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "permitted": bool,
  "ownership_cap": float (0-100),
  "approvals_needed": ["authority1", "authority2"],
  "conditions": ["condition1", "condition2"],
  "timeline_months": int,
  "key_risks": ["risk1", "risk2"],
  "compliance_complexity": "low/medium/high"
}}
"""

GEOPOLITICAL_RISK_PROMPT = """
You are a geopolitical risk analyst assessing country risk.

===== COMPANY =====
{company}

===== TARGET COUNTRY =====
{country}

===== INDUSTRY =====
{industry}

===== POLITICAL RISK DATA =====
{political_data}

===== ECONOMIC DATA =====
{economic_data}

===== RECENT NEWS =====
{news}

===== TASK =====
Assess geopolitical and macroeconomic risks:

**1. Political Stability**
- Government stability and policy continuity
- Political transitions and elections
- Geopolitical tensions

**2. Economic Outlook**
- GDP growth trends
- Inflation and currency stability
- Economic diversification

**3. Social Factors**
- Consumer sentiment
- Social stability
- Cultural considerations

**4. Regulatory Trends**
- Policy direction (pro-business vs restrictive)
- Recent regulatory changes
- Future policy outlook

**5. Bilateral Relations**
- Relationship with source country
- Trade relations
- Diplomatic ties

Provide risk assessment with overall risk level and key factors.

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "stability_score": float (1-10),
  "key_risks": ["risk1", "risk2", "risk3"],
  "political_trends": ["trend1", "trend2"],
  "economic_outlook": "positive/neutral/negative",
  "currency_volatility": "low/medium/high",
  "bilateral_relations": "strong/moderate/weak",
  "overall_risk_level": "low/medium/high/critical"
}}
"""

REGULATORY_RISK_MATRIX_PROMPT = """
You are a risk management consultant creating a comprehensive risk matrix.

===== STRATEGY =====
{strategy}

===== REGULATORY FINDINGS =====

**FDI Analysis:**
{fdi}

**Tax Analysis:**
{tax}

**Trade Barriers:**
{trade}

**Labor Regulations:**
{labor}

**Geopolitical Assessment:**
{geopolitical}

===== TASK =====
Create a comprehensive regulatory risk matrix.

For EACH significant risk:

1. **Risk Description**: Clear, specific description
2. **Probability** (1-5):
   - 1 = Very Low (<10%)
   - 2 = Low (10-30%)
   - 3 = Medium (30-50%)
   - 4 = High (50-70%)
   - 5 = Very High (>70%)

3. **Impact** (1-5):
   - 1 = Minimal (minor delay/cost)
   - 2 = Low (manageable)
   - 3 = Medium (significant but not critical)
   - 4 = High (major impact)
   - 5 = Critical (strategy blocker)

4. **Risk Score** = Probability × Impact

5. **Mitigation Strategy**: How to reduce or manage the risk

**Risk Classification**:
- 1-6: Low risk
- 7-12: Medium risk
- 13-20: High risk
- 21-25: Critical risk

**Overall Assessment**: Classify total regulatory risk as Low / Medium / High / Critical

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "risks": [
    {{
      "risk": "Risk description",
      "category": "fdi/tax/trade/labor/geopolitical",
      "probability": int (1-5),
      "impact": int (1-5),
      "score": int,
      "mitigation": "Mitigation strategy"
    }}
  ],
  "total_risk_score": int,
  "risk_level": "low/medium/high/critical",
  "critical_risks": ["risk1", "risk2"]
}}
"""

LEGAL_STRUCTURE_PROMPT = """
You are a corporate structuring advisor recommending optimal legal entity.

===== COMPANY & STRATEGY =====
Company: {company}
Strategy: {strategy}

===== REGULATORY ANALYSIS =====
{regulatory_summary}

===== BUSINESS REQUIREMENTS =====
{business_requirements}

===== TASK =====
Recommend the optimal legal structure considering:

**1. Control Requirements**
- Need for full operational control
- Decision-making autonomy

**2. Liability Protection**
- Limited liability vs unlimited
- Asset protection

**3. Tax Efficiency**
- Effective tax rate
- Repatriation ease
- Treaty benefits

**4. Operational Flexibility**
- Ease of operations
- Regulatory compliance burden

**5. Exit Strategy**
- Ease of exit
- Asset liquidation

**STRUCTURE OPTIONS**:

1. **Wholly-Owned Subsidiary**
   - Full control, full liability protection
   - Higher setup cost, full compliance burden

2. **Joint Venture (Local Partner)**
   - Shared control, local expertise
   - Partner risk, profit sharing

3. **Branch Office**
   - Direct extension, no separate entity
   - Lower setup cost, unlimited liability

4. **Representative Office**
   - Limited activities, no revenue generation
   - Lowest cost, restricted operations

5. **Licensing/Franchising**
   - Minimal investment, royalty income
   - Limited control, brand risk

Recommend structure with clear rationale, pros/cons, timeline, and costs.

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "recommended_structure": "structure name",
  "rationale": "2-3 sentence explanation",
  "pros": ["pro1", "pro2", "pro3"],
  "cons": ["con1", "con2"],
  "alternatives": [
    {{
      "structure": "alternative name",
      "when_to_consider": "scenario"
    }}
  ],
  "setup_timeline": "X-Y months",
  "estimated_cost": "$X-$Y",
  "ongoing_compliance": ["requirement1", "requirement2"]
}}
"""

SECTOR_REGULATIONS_PROMPT = """
Analyze sector-specific regulations for {industry} in {country}.

===== CONTEXT =====
{context}

===== TASK =====
Identify:

1. **Licenses Required**
   - Operating licenses
   - Sector-specific permits
   - Professional certifications

2. **Regulatory Bodies**
   - Primary regulator
   - Secondary authorities
   - Enforcement agencies

3. **Compliance Obligations**
   - Reporting requirements
   - Audit obligations
   - Record-keeping

4. **Operational Restrictions**
   - Service limitations
   - Geographic restrictions
   - Pricing controls

5. **Penalties**
   - Violation consequences
   - Fine structures

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "licenses_required": ["license1", "license2"],
  "regulatory_bodies": ["body1", "body2"],
  "compliance_cost": "low/medium/high",
  "ongoing_obligations": ["obligation1", "obligation2"],
  "penalties_for_violation": ["penalty1", "penalty2"],
  "time_to_obtain_licenses": "X months"
}}
"""
