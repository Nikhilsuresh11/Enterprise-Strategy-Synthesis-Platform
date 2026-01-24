"""Enterprise-Grade Intent Analyzer with Professional Strategic Thinking."""

from typing import Dict, Any, List, Optional
from app.agents.base import BaseAgent
from app.models.state import AgentState
from app.services.llm_service import LLMService
from app.utils.logger import get_logger
from app.utils.strategic_frameworks import (
    AnalysisType,
    StrategicFramework,
    FrameworkLibrary,
    FRAMEWORK_PROMPTS
)
import json
import re

logger = get_logger(__name__)


class EnterpriseIntentAnalyzer(BaseAgent):
    """
    MBB-Grade Intent Analyzer.
    
    Implements structured, hypothesis-driven analysis approach:
    1. Deep context extraction
    2. Hypothesis formation
    3. Issue tree construction
    4. Framework selection
    5. Strategic prompt generation
    """
    
    def __init__(self, llm: LLMService):
        super().__init__("enterprise_intent_analyzer")
        self.llm = llm
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute enterprise-grade intent analysis.
        
        Args:
            state: Current agent state with chat_history
        
        Returns:
            State with enriched context, hypotheses, and strategic prompts
        """
        chat_history = state.get("chat_history", [])
        company_name = state["request"]["company_name"]
        question = state["request"].get("question", "")
        companies = state["request"].get("companies", [company_name])
        analysis_type = state["request"].get("analysis_type", "single")
        
        # If no chat history, generate fallback prompts based on analysis type
        if not chat_history or len(chat_history) < 2:
            logger.warning("minimal_chat_history", company=company_name, chat_length=len(chat_history))
            
            # Generate appropriate prompts based on analysis type
            if analysis_type == "comparison" and len(companies) > 1:
                state["dynamic_prompts"] = self._generate_comparative_prompts(companies)
                logger.info("comparative_prompts_generated", companies=companies)
            elif analysis_type == "joint_venture" and len(companies) > 1:
                state["dynamic_prompts"] = self._generate_joint_venture_prompts(companies)
                logger.info("joint_venture_prompts_generated", companies=companies)
            else:
                state["dynamic_prompts"] = self._generate_fallback_prompts(company_name, question)
                logger.info("fallback_prompts_generated", company=company_name)
            
            state["user_intent"] = {"type": analysis_type, "fallback": True}
            
            return state
        
        logger.info("enterprise_intent_analysis_starting", company=company_name)
        
        try:
            # Step 1: Deep Context Extraction
            context = await self._extract_business_context(chat_history, company_name)
            state["business_context"] = context
            
            # Step 2: Hypothesis Formation
            hypotheses = await self._form_strategic_hypotheses(context, company_name)
            state["strategic_hypotheses"] = hypotheses
            
            # Step 3: Issue Tree Construction
            issue_tree = await self._build_issue_tree(context, hypotheses, company_name)
            state["issue_tree"] = issue_tree
            
            # Step 4: Framework Selection
            frameworks = self._select_frameworks(context)
            state["selected_frameworks"] = frameworks
            
            # Step 5: Generate Framework-Based Prompts
            prompts = await self._generate_strategic_prompts(
                context, hypotheses, issue_tree, frameworks, company_name
            )
            state["dynamic_prompts"] = prompts
            
            # Also set user_intent for backward compatibility
            state["user_intent"] = {
                "type": context.get("analysis_type", "general_research"),
                "sophistication": "enterprise_grade"
            }
            
            logger.info(
                "enterprise_intent_analysis_completed",
                company=company_name,
                analysis_type=context.get("analysis_type"),
                frameworks_count=len(frameworks),
                hypotheses_count=len(hypotheses.get("sub_hypotheses", []))
            )
            
        except Exception as e:
            logger.error("enterprise_intent_analysis_failed", error=str(e), exc_info=True)
            # Fallback to basic analysis
            state["user_intent"] = {"type": "general_research"}
            state["dynamic_prompts"] = {}
        
        return state
    
    async def _extract_business_context(
        self,
        chat_history: List[Dict[str, str]],
        company_name: str
    ) -> Dict[str, Any]:
        """Extract deep business context from conversation."""
        
        chat_text = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'AI'}: {msg['content']}"
            for msg in chat_history
        ])
        
        prompt = f"""Analyze this conversation about {company_name} and extract rich business context.

Conversation:
{chat_text}

Extract and return ONLY a JSON object with this structure:
{{
    "analysis_type": "investment_decision|competitive_intelligence|partnership_evaluation|market_entry|mna_analysis|general_research",
    "core_question": "The main business question being asked",
    "decision_criteria": ["criterion1", "criterion2"],
    "user_profile": {{
        "role": "investor|competitor|partner|analyst|executive",
        "sophistication": "beginner|intermediate|advanced|expert",
        "time_horizon": "immediate|short_term|medium_term|long_term",
        "risk_tolerance": "conservative|moderate|aggressive"
    }},
    "company_context": {{
        "industry": "Primary industry",
        "market_position": "leader|challenger|follower|niche",
        "stage": "startup|growth|mature|declining",
        "geography": "Primary geographic focus"
    }},
    "priority_areas": ["area1", "area2", "area3"],
    "specific_concerns": ["concern1", "concern2"]
}}

Focus on understanding the strategic intent and business context.
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            task_type="reasoning",
            temperature=0.2,
            max_tokens=800
        )
        
        return self._parse_json_response(response, "context_extraction")
    
    async def _form_strategic_hypotheses(
        self,
        context: Dict[str, Any],
        company_name: str
    ) -> Dict[str, Any]:
        """Form strategic hypotheses like a professional consultant."""
        
        analysis_type = context.get("analysis_type", "general_research")
        core_question = context.get("core_question", f"Analyze {company_name}")
        
        prompt = f"""You are a professional strategy consultant. Form strategic hypotheses for this analysis.

Company: {company_name}
Analysis Type: {analysis_type}
Core Question: {core_question}
Context: {json.dumps(context, indent=2)}

Generate strategic hypotheses following professional consulting methodology. Return ONLY a JSON object:
{{
    "primary_hypothesis": "Main hypothesis that answers the core question",
    "sub_hypotheses": [
        {{
            "area": "market_position|financial_health|growth_potential|competitive_advantage",
            "hypothesis": "Specific, testable hypothesis",
            "key_questions": ["question1", "question2", "question3"],
            "priority": "high|medium|low"
        }}
    ],
    "critical_assumptions": ["assumption1", "assumption2", "assumption3"],
    "success_criteria": ["How to measure if hypothesis is validated"]
}}

Make hypotheses:
- Specific and testable
- Tied to the core business question
- Based on strategic frameworks
- Prioritized by impact
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            task_type="reasoning",
            temperature=0.3,
            max_tokens=1000
        )
        
        return self._parse_json_response(response, "hypothesis_formation")
    
    async def _build_issue_tree(
        self,
        context: Dict[str, Any],
        hypotheses: Dict[str, Any],
        company_name: str
    ) -> Dict[str, Any]:
        """Build MECE issue tree for structured analysis."""
        
        core_question = context.get("core_question", f"Analyze {company_name}")
        
        prompt = f"""You are a professional strategy consultant. Build a MECE (Mutually Exclusive, Collectively Exhaustive) issue tree.

Company: {company_name}
Core Question: {core_question}
Hypotheses: {json.dumps(hypotheses, indent=2)}

Create an issue tree that breaks down the problem systematically. Return ONLY a JSON object:
{{
    "root_question": "{core_question}",
    "level_1_branches": [
        {{
            "branch": "Major area (e.g., Growth Potential, Competitive Position)",
            "sub_questions": ["Specific question 1", "Specific question 2"],
            "priority": "high|medium|low",
            "analysis_approach": "How to analyze this branch"
        }}
    ],
    "critical_path": ["Most important questions that drive the decision"],
    "mece_validation": "Explanation of how this is MECE"
}}

Ensure:
- Branches are mutually exclusive (no overlap)
- Branches are collectively exhaustive (cover everything)
- Questions are specific and answerable
- Critical path is identified
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            task_type="reasoning",
            temperature=0.2,
            max_tokens=1200
        )
        
        return self._parse_json_response(response, "issue_tree_construction")
    
    def _select_frameworks(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Select appropriate strategic frameworks for analysis."""
        
        analysis_type_str = context.get("analysis_type", "general_research")
        
        # Map string to enum
        try:
            analysis_type = AnalysisType(analysis_type_str)
        except ValueError:
            analysis_type = AnalysisType.GENERAL_RESEARCH
        
        # Get recommended frameworks
        framework_enums = FrameworkLibrary.get_frameworks_for_analysis(analysis_type)
        
        # Get framework details
        frameworks = []
        for framework_enum in framework_enums:
            details = FrameworkLibrary.get_framework_details(framework_enum)
            frameworks.append({
                "framework": framework_enum.value,
                "name": details.get("name"),
                "purpose": details.get("purpose"),
                "components": details.get("components", [])
            })
        
        logger.info(
            "frameworks_selected",
            analysis_type=analysis_type_str,
            frameworks=[f["name"] for f in frameworks]
        )
        
        return frameworks
    
    async def _generate_strategic_prompts(
        self,
        context: Dict[str, Any],
        hypotheses: Dict[str, Any],
        issue_tree: Dict[str, Any],
        frameworks: List[Dict[str, Any]],
        company_name: str
    ) -> Dict[str, str]:
        """Generate framework-based prompts for each agent."""
        
        prompts = {}
        
        # Company Profiling - Use Value Chain
        value_chain_prompt = FRAMEWORK_PROMPTS.get(StrategicFramework.VALUE_CHAIN, "")
        prompts["company_profiling"] = value_chain_prompt.format(company_name=company_name).strip()
        
        # Market Research - Use Porter's 5 Forces
        porters_prompt = FRAMEWORK_PROMPTS.get(StrategicFramework.PORTERS_FIVE_FORCES, "")
        prompts["market_research"] = porters_prompt.format(company_name=company_name).strip()
        
        # Financial Analysis - Use DuPont
        dupont_prompt = FRAMEWORK_PROMPTS.get(StrategicFramework.DUPONT_ANALYSIS, "")
        prompts["financial_analysis"] = dupont_prompt.format(company_name=company_name).strip()
        
        # Risk Assessment - Custom strategic risk prompt
        prompts["risk_assessment"] = await self._generate_risk_prompt(
            context, hypotheses, company_name
        )
        
        # Strategy Synthesis - Use Ansoff + SWOT
        prompts["strategy_synthesis"] = await self._generate_strategy_prompt(
            context, hypotheses, issue_tree, company_name
        )
        
        # Validation - Quality assurance prompt
        prompts["validation"] = await self._generate_validation_prompt(
            context, hypotheses, company_name
        )
        
        return prompts
    
    async def _generate_risk_prompt(
        self,
        context: Dict[str, Any],
        hypotheses: Dict[str, Any],
        company_name: str
    ) -> str:
        """Generate strategic risk assessment prompt."""
        
        return f"""Assess strategic risks for {company_name} using structured framework:

1. STRATEGIC RISKS (High Impact):
   - Technology disruption threats
   - Competitive threats and market share loss
   - Market saturation or demand shifts
   - Business model vulnerabilities

2. OPERATIONAL RISKS (Medium Impact):
   - Execution and delivery risks
   - Supply chain vulnerabilities
   - Talent and organizational risks
   - Quality and reputation risks

3. FINANCIAL RISKS:
   - Valuation and pricing risks
   - Capital structure and liquidity
   - Cost structure sustainability
   - Revenue concentration

4. EXTERNAL RISKS:
   - Regulatory and policy changes
   - Macroeconomic factors
   - Geopolitical risks
   - Industry disruption

5. ESG RISKS:
   - Environmental impact and sustainability
   - Social and labor practices
   - Governance and leadership

For each risk category:
- Identify top 2-3 specific risks
- Assess likelihood (Low/Medium/High)
- Assess impact (Low/Medium/High)
- Note potential mitigation strategies

Return 4-5 bullet points on the most critical risks with severity and mitigation approaches.
"""
    
    async def _generate_strategy_prompt(
        self,
        context: Dict[str, Any],
        hypotheses: Dict[str, Any],
        issue_tree: Dict[str, Any],
        company_name: str
    ) -> str:
        """Generate strategic synthesis prompt."""
        
        analysis_type = context.get("analysis_type", "general_research")
        core_question = context.get("core_question", f"Analyze {company_name}")
        
        return f"""Synthesize strategic recommendation for {company_name}.

Core Question: {core_question}
Analysis Type: {analysis_type}

1. STRATEGIC POSITION ASSESSMENT:
   - Where does {company_name} stand today?
   - What are the strategic inflection points?
   - What is the strategic trajectory?

2. GROWTH STRATEGY (Ansoff Matrix):
   - Market Penetration: Increasing share in existing markets
   - Market Development: Geographic or segment expansion
   - Product Development: New products for existing customers
   - Diversification: New products in new markets

3. STRATEGIC OPTIONS:
   - Option A: [Primary recommendation with rationale]
   - Option B: [Alternative approach]
   - Option C: [Contingency plan]

4. DECISION CRITERIA SCORING:
   - Growth potential: X/10
   - Competitive position: X/10
   - Financial attractiveness: X/10
   - Risk-adjusted return: X/10
   - Strategic fit: X/10

5. RECOMMENDATION:
   - Clear strategic thesis
   - Key value drivers
   - Critical success factors
   - Key risks and mitigations
   - Monitoring metrics

Return 4-5 strategic recommendations with clear rationale and action priorities.
"""
    
    async def _generate_validation_prompt(
        self,
        context: Dict[str, Any],
        hypotheses: Dict[str, Any],
        company_name: str
    ) -> str:
        """Generate validation prompt for quality assurance."""
        
        return f"""Validate the strategic analysis for {company_name}.

Quality Assurance Checks:

1. COMPLETENESS:
   - Are all critical questions addressed?
   - Are there gaps in the analysis?
   - What additional data would strengthen conclusions?

2. CONSISTENCY:
   - Do conclusions align across different analyses?
   - Are there contradictions to resolve?
   - Is the logic sound throughout?

3. STRATEGIC RIGOR:
   - Are frameworks applied correctly?
   - Are hypotheses tested adequately?
   - Is the analysis MECE (Mutually Exclusive, Collectively Exhaustive)?

4. ACTIONABILITY:
   - Are recommendations specific and actionable?
   - Are success metrics defined?
   - Is the implementation path clear?

5. CONFIDENCE ASSESSMENT:
   - What is the confidence level in key conclusions?
   - What are the key uncertainties?
   - What could change the recommendation?

Return 3-4 bullet points on:
- Overall quality score (1-10)
- Key strengths of the analysis
- Critical gaps or concerns
- Confidence level and caveats
"""
    
    def _generate_fallback_prompts(self, company_name: str, question: str) -> Dict[str, str]:
        """
        Generate basic framework prompts when chat history is minimal.
        
        Uses company name and question keywords to select appropriate frameworks.
        
        Args:
            company_name: Name of the company to analyze
            question: Analysis question or context
        
        Returns:
            Dictionary of agent prompts with basic framework guidance
        """
        prompts = {}
        question_lower = question.lower() if question else ""
        
        # Always include core frameworks
        prompts["company_profiling"] = FRAMEWORK_PROMPTS.get(
            StrategicFramework.VALUE_CHAIN, ""
        ).format(company_name=company_name).strip()
        
        prompts["market_research"] = FRAMEWORK_PROMPTS.get(
            StrategicFramework.PORTERS_FIVE_FORCES, ""
        ).format(company_name=company_name).strip()
        
        prompts["financial_analysis"] = FRAMEWORK_PROMPTS.get(
            StrategicFramework.DUPONT_ANALYSIS, ""
        ).format(company_name=company_name).strip()
        
        # Risk assessment - basic prompt
        prompts["risk_assessment"] = f"""Assess key risks for {company_name} using Risk Matrix framework (Severity × Likelihood).

Identify 4-5 critical risks across:
- Strategic risks (market, competition, disruption)
- Operational risks (execution, supply chain, talent)
- Financial risks (liquidity, profitability, valuation)
- External risks (regulatory, macro, geopolitical)

For each risk, specify:
- Risk name and description
- Severity (high/medium/low)
- Likelihood (high/medium/low)
- Mitigation strategy

Return structured analysis with specific, actionable insights."""
        
        # Strategy synthesis - basic prompt
        prompts["strategy_synthesis"] = f"""Synthesize strategic recommendations for {company_name} using Ansoff Matrix and SWOT.

Ansoff Matrix Analysis:
- Market Penetration opportunities
- Market Development potential
- Product Development options
- Diversification strategies

SWOT Summary:
- Top strength
- Top weakness
- Top opportunity
- Top threat

Provide 4-5 specific, actionable strategic recommendations with clear rationale."""
        
        # Validation - basic prompt
        prompts["validation"] = f"""Validate the strategic analysis for {company_name}.

Quality Checks:
1. Framework Alignment: Are strategic frameworks applied correctly?
2. Data Consistency: Is the analysis internally consistent?
3. Actionability: Are recommendations specific and implementable?
4. MECE Compliance: Is the structure mutually exclusive and collectively exhaustive?

Provide:
- Confidence score (0-1)
- Quality assessment
- Critical gaps (if any)
- Overall validation status"""
        
        logger.info(
            "fallback_prompts_created",
            company=company_name,
            frameworks=["Value Chain", "Porter's 5 Forces", "DuPont ROE", "Risk Matrix", "Ansoff + SWOT"]
        )
        
        return prompts
    
    def _parse_json_response(self, response: str, context: str) -> Dict[str, Any]:
        """Parse JSON from LLM response with fallback."""
        
        try:
            # Try direct parsing
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown or text
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            logger.warning(f"{context}_json_parse_failed", response_preview=response[:200])
            return {}
    def _generate_comparative_prompts(self, companies: List[str]) -> Dict[str, str]:
        """Generate prompts for comparative analysis of multiple companies."""
        company_list = " vs ".join(companies)
        prompts = {}
        
        prompts["company_profiling"] = f"""Compare {company_list} using Value Chain Analysis.
For EACH company, analyze Primary Activities, Support Activities, and Value Creation.
Provide SIDE-BY-SIDE comparison highlighting key differences and where each excels."""

        prompts["market_research"] = f"""Compare {company_list} using Porter's 5 Forces.
For each force, compare how it affects each company. Highlight which has stronger position."""

        prompts["financial_analysis"] = f"""Compare {company_list} using DuPont ROE Analysis.
Provide comparative table showing profitability, asset efficiency, and leverage for EACH company."""

        prompts["risk_assessment"] = f"""Compare risks for {company_list} using Risk Matrix.
Identify 3-4 critical risks for EACH company. Compare which faces higher risks."""

        prompts["strategy_synthesis"] = f"""Synthesize comparative recommendations for {company_list}.
Provide SIDE-BY-SIDE SWOT, Ansoff positioning, and INVESTMENT RECOMMENDATION (which is better)."""

        prompts["validation"] = f"""Validate comparative analysis of {company_list}.
Check if comparisons are fair, balanced, and data is comparable."""

        return prompts
    
    def _generate_joint_venture_prompts(self, companies: List[str]) -> Dict[str, str]:
        """Generate prompts for joint venture/partnership analysis."""
        company_list = " + ".join(companies)
        prompts = {}
        
        prompts["company_profiling"] = f"""Analyze JV potential between {company_list}.
Identify complementary capabilities, synergies, and combined value proposition."""

        prompts["market_research"] = f"""Analyze market potential for {company_list} JV.
Assess combined market position, customer reach, and competitive advantages."""

        prompts["financial_analysis"] = f"""Assess financial viability of {company_list} JV.
Analyze combined financial power, synergy value, cost savings, and ROI projections."""

        prompts["risk_assessment"] = f"""Identify risks for {company_list} JV.
Cover partnership risks, cultural alignment, integration challenges, and mitigation strategies."""

        prompts["strategy_synthesis"] = f"""Synthesize JV recommendation for {company_list}.
Provide strategic rationale, JV structure, and GO/NO-GO recommendation with clear reasoning."""

        prompts["validation"] = f"""Validate JV analysis for {company_list}.
Check if strategic rationale is compelling, synergies realistic, and recommendation clear."""

        return prompts
