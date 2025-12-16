"""Prompt templates for Synthesizer Agent."""

EXECUTIVE_SUMMARY_PROMPT = """
You are a Partner at McKinsey & Company creating an executive summary.

===== STRATEGIC QUESTION =====
{question}

===== RESEARCH FINDINGS =====
{research_summary}

===== MARKET ANALYSIS =====
• TAM: ${tam}M
• SAM: ${sam}M  
• SOM (Year 5): ${som}M
• Competitive Landscape: {competitive_summary}

===== FINANCIAL MODEL =====
• Expected Revenue (Year 5): ${revenue_y5}M
• LTV/CAC Ratio: {ltv_cac_ratio}x
• Unit Economics: {unit_econ_assessment}
• Valuation (DCF): ${valuation}M

===== REGULATORY ASSESSMENT =====
• Overall Risk Level: {regulatory_risk}
• Key Blockers: {blockers}
• Recommended Structure: {legal_structure}

===== TASK =====
Based on this comprehensive analysis, provide a McKinsey-grade executive summary:

**1. FINAL RECOMMENDATION**: Choose ONE:
   - "proceed" = Strong positive case, manageable risks, clear path forward
   - "decline" = Risks outweigh benefits, better alternatives exist
   - "conditional" = Viable if specific conditions are met

**2. CONFIDENCE LEVEL**: 0.0 to 1.0 (how confident are you in this recommendation)

**3. THREE SUPPORTING POINTS**: Why this recommendation is correct (data-backed)

**4. THREE KEY RISKS**: What could go wrong (be specific)

**5. EXPECTED IMPACT**: If recommendation is followed, what happens?

**6. TIMELINE**: When will results be realized?

**7. CONDITIONS**: If "conditional", what must be true? (empty list if not conditional)

Use clear, executive-friendly language. Be decisive and data-driven.

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "recommendation": "proceed/decline/conditional",
  "confidence": float (0.0-1.0),
  "supporting_points": ["point1", "point2", "point3"],
  "key_risks": ["risk1", "risk2", "risk3"],
  "expected_impact": "string",
  "timeline": "string",
  "conditions": ["condition1", "condition2"] or []
}}
"""

RECOMMENDATION_SYNTHESIS_PROMPT = """
You are a strategy consultant making a final recommendation.

===== DECISION FRAMEWORK =====
Use weighted scoring to determine recommendation:

**Scores (1-10)**:
• Market Opportunity: {market_score}/10
• Financial Attractiveness: {financial_score}/10
• Regulatory Feasibility: {regulatory_score}/10
• Strategic Fit: {strategic_score}/10

**Risk Level**: {risk_level} (low/medium/high/critical)

**WEIGHTED SCORE CALCULATION**:
= (Market × 0.30) + (Financial × 0.30) + (Regulatory × 0.25) + (Strategic × 0.15)

**DECISION RULES**:
- If Score > 7.0 AND Risk ≠ Critical → PROCEED
- If Score < 5.0 OR Risk = Critical → DECLINE  
- If 5.0 ≤ Score ≤ 7.0 → CONDITIONAL

**Your calculated score**: {calculated_score:.1f}/10

Provide recommendation with detailed rationale explaining why this score leads to your decision.

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "recommendation": "proceed/decline/conditional",
  "rationale": "2-3 sentence explanation",
  "weighted_score": float,
  "key_decision_factors": ["factor1", "factor2", "factor3"]
}}
"""

SLIDE_GENERATION_PROMPT = """
You are creating consulting-grade slide content for McKinsey.

===== SLIDE DETAILS =====
Slide #{slide_num}: {slide_title}

===== ANALYSIS CONTEXT =====
{analysis_context}

===== TASK =====
Generate content for this slide following McKinsey standards:

**1. KEY MESSAGE**: One sentence that captures the slide's core insight (the "so what?")

**2. CONTENT**: 3-5 bullet points
   - Start with action verbs or strong statements
   - Include specific numbers/data points
   - Each bullet must answer "why does this matter?"
   - Max 10 words per bullet headline
   - Use sub-bullets for supporting details

**3. SPEAKER NOTES**: 2-3 sentences for presenting this slide

**Consulting Style Guidelines**:
✓ Be concise and impactful
✓ Lead with insights, not just facts
✓ Use the "So What?" test
✓ Quantify whenever possible
✓ Action-oriented language

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "key_message": "string",
  "content": ["bullet1", "bullet2", "bullet3"],
  "speaker_notes": "string"
}}
"""

IMPLEMENTATION_ROADMAP_PROMPT = """
Create a 6-12 month implementation roadmap for {strategy}.

===== CONTEXT =====
Recommendation: {recommendation}
Timeline: {timeline}
Key Requirements: {requirements}

===== TASK =====
Create a phased implementation plan:

**Phase 1: Preparation (Months 1-3)**
- Regulatory approvals
- Entity setup
- Team building

**Phase 2: Launch (Months 4-6)**  
- Market entry
- Initial operations
- Customer acquisition

**Phase 3: Scale (Months 7-12)**
- Expansion
- Optimization
- Market penetration

For EACH phase, provide:
1. **Milestones**: Key achievements
2. **Key Activities**: What needs to be done
3. **Resources Required**: Team, budget, infrastructure
4. **Success Metrics**: How to measure progress
5. **Risks**: What could delay this phase

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "phases": [
    {{
      "phase": "Preparation (Months 1-3)",
      "duration": "3 months",
      "milestones": ["milestone1", "milestone2"],
      "key_activities": ["activity1", "activity2"],
      "resources_required": ["resource1", "resource2"],
      "success_metrics": ["metric1", "metric2"],
      "risks": ["risk1", "risk2"]
    }}
  ]
}}
"""

ALTERNATIVES_PROMPT = """
The primary recommendation is to DECLINE the proposed strategy.

===== DECLINED STRATEGY =====
{declined_strategy}

===== REASON FOR DECLINE =====
{decline_reason}

===== TASK =====
Propose 2-3 alternative strategies that could achieve similar objectives with better risk/reward profiles.

For each alternative:
1. **Alternative Strategy**: Clear description
2. **Rationale**: Why this is better than the declined option
3. **Pros**: Key advantages (3-4 points)
4. **Cons**: Key disadvantages (2-3 points)
5. **Estimated Timeline**: How long to execute
6. **Resource Requirements**: What's needed

**OUTPUT FORMAT**: Return ONLY valid JSON:

{{
  "alternatives": [
    {{
      "strategy": "string",
      "rationale": "string",
      "pros": ["pro1", "pro2", "pro3"],
      "cons": ["con1", "con2"],
      "timeline": "string",
      "resources": "string"
    }}
  ]
}}
"""
