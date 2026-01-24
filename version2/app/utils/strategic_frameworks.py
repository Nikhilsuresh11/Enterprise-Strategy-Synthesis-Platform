"""Strategic Frameworks Library for Professional Analysis."""

from typing import Dict, List, Any
from enum import Enum


class AnalysisType(Enum):
    """Types of strategic analysis."""
    INVESTMENT_DECISION = "investment_decision"
    COMPETITIVE_INTELLIGENCE = "competitive_intelligence"
    PARTNERSHIP_EVALUATION = "partnership_evaluation"
    MARKET_ENTRY = "market_entry"
    MNA_ANALYSIS = "mna_analysis"
    GENERAL_RESEARCH = "general_research"


class StrategicFramework(Enum):
    """Strategic frameworks for analysis."""
    PORTERS_FIVE_FORCES = "porters_five_forces"
    VALUE_CHAIN = "value_chain"
    SWOT = "swot"
    DUPONT_ANALYSIS = "dupont_analysis"
    BCG_MATRIX = "bcg_matrix"
    ANSOFF_MATRIX = "ansoff_matrix"
    MCKINSEY_7S = "mckinsey_7s"
    PESTEL = "pestel"
    VRIO = "vrio"
    BLUE_OCEAN = "blue_ocean"


class FrameworkLibrary:
    """Library of strategic frameworks and their applications."""
    
    # Framework definitions
    FRAMEWORKS = {
        StrategicFramework.PORTERS_FIVE_FORCES: {
            "name": "Porter's Five Forces",
            "purpose": "Analyze competitive dynamics and market attractiveness",
            "components": [
                "Competitive Rivalry",
                "Threat of New Entrants",
                "Bargaining Power of Suppliers",
                "Bargaining Power of Buyers",
                "Threat of Substitutes"
            ],
            "best_for": ["market_analysis", "competitive_position", "industry_attractiveness"],
            "output": "Market attractiveness score and competitive intensity assessment"
        },
        
        StrategicFramework.VALUE_CHAIN: {
            "name": "Value Chain Analysis",
            "purpose": "Identify sources of competitive advantage and value creation",
            "components": [
                "Inbound Logistics",
                "Operations",
                "Outbound Logistics",
                "Marketing & Sales",
                "Service",
                "Firm Infrastructure",
                "HR Management",
                "Technology Development",
                "Procurement"
            ],
            "best_for": ["competitive_advantage", "cost_analysis", "differentiation"],
            "output": "Key value drivers and competitive moats"
        },
        
        StrategicFramework.DUPONT_ANALYSIS: {
            "name": "DuPont ROE Analysis",
            "purpose": "Decompose financial performance drivers",
            "components": [
                "Net Profit Margin",
                "Asset Turnover",
                "Financial Leverage",
                "ROE Decomposition"
            ],
            "best_for": ["financial_health", "profitability_analysis", "efficiency"],
            "output": "ROE drivers and financial efficiency metrics"
        },
        
        StrategicFramework.SWOT: {
            "name": "SWOT Analysis",
            "purpose": "Assess strategic position and opportunities",
            "components": [
                "Strengths (Internal, Positive)",
                "Weaknesses (Internal, Negative)",
                "Opportunities (External, Positive)",
                "Threats (External, Negative)"
            ],
            "best_for": ["strategic_position", "opportunity_identification", "risk_assessment"],
            "output": "Strategic positioning and action priorities"
        },
        
        StrategicFramework.ANSOFF_MATRIX: {
            "name": "Ansoff Growth Matrix",
            "purpose": "Evaluate growth strategy options",
            "components": [
                "Market Penetration",
                "Market Development",
                "Product Development",
                "Diversification"
            ],
            "best_for": ["growth_strategy", "expansion_planning", "strategic_options"],
            "output": "Growth strategy recommendations with risk assessment"
        },
        
        StrategicFramework.PESTEL: {
            "name": "PESTEL Analysis",
            "purpose": "Analyze macro-environmental factors",
            "components": [
                "Political",
                "Economic",
                "Social",
                "Technological",
                "Environmental",
                "Legal"
            ],
            "best_for": ["market_entry", "risk_assessment", "external_analysis"],
            "output": "Macro trends and their strategic implications"
        },
        
        StrategicFramework.VRIO: {
            "name": "VRIO Framework",
            "purpose": "Assess sustainable competitive advantages",
            "components": [
                "Value: Does it create value?",
                "Rarity: Is it rare?",
                "Imitability: Is it hard to imitate?",
                "Organization: Is it organized to capture value?"
            ],
            "best_for": ["competitive_advantage", "moat_analysis", "sustainability"],
            "output": "Sustainable competitive advantages and their defensibility"
        }
    }
    
    # Framework selection rules
    FRAMEWORK_MAPPING = {
        AnalysisType.INVESTMENT_DECISION: [
            StrategicFramework.DUPONT_ANALYSIS,
            StrategicFramework.PORTERS_FIVE_FORCES,
            StrategicFramework.SWOT,
            StrategicFramework.VRIO
        ],
        AnalysisType.COMPETITIVE_INTELLIGENCE: [
            StrategicFramework.PORTERS_FIVE_FORCES,
            StrategicFramework.VALUE_CHAIN,
            StrategicFramework.VRIO,
            StrategicFramework.SWOT
        ],
        AnalysisType.PARTNERSHIP_EVALUATION: [
            StrategicFramework.VALUE_CHAIN,
            StrategicFramework.SWOT,
            StrategicFramework.VRIO
        ],
        AnalysisType.MARKET_ENTRY: [
            StrategicFramework.PORTERS_FIVE_FORCES,
            StrategicFramework.PESTEL,
            StrategicFramework.ANSOFF_MATRIX,
            StrategicFramework.SWOT
        ],
        AnalysisType.MNA_ANALYSIS: [
            StrategicFramework.DUPONT_ANALYSIS,
            StrategicFramework.VALUE_CHAIN,
            StrategicFramework.SWOT,
            StrategicFramework.VRIO
        ],
        AnalysisType.GENERAL_RESEARCH: [
            StrategicFramework.SWOT,
            StrategicFramework.PORTERS_FIVE_FORCES,
            StrategicFramework.VALUE_CHAIN
        ]
    }
    
    @classmethod
    def get_frameworks_for_analysis(cls, analysis_type: AnalysisType) -> List[StrategicFramework]:
        """Get recommended frameworks for analysis type."""
        return cls.FRAMEWORK_MAPPING.get(analysis_type, [
            StrategicFramework.SWOT,
            StrategicFramework.PORTERS_FIVE_FORCES
        ])
    
    @classmethod
    def get_framework_details(cls, framework: StrategicFramework) -> Dict[str, Any]:
        """Get details for a specific framework."""
        return cls.FRAMEWORKS.get(framework, {})
    
    @classmethod
    def get_all_frameworks(cls) -> Dict[StrategicFramework, Dict[str, Any]]:
        """Get all available frameworks."""
        return cls.FRAMEWORKS


# Prompt templates for each framework
FRAMEWORK_PROMPTS = {
    StrategicFramework.PORTERS_FIVE_FORCES: """
Analyze {company_name}'s market using Porter's Five Forces:

1. COMPETITIVE RIVALRY:
   - Who are the key competitors?
   - What is the intensity of competition?
   - How is market share distributed?
   - What are the competitive dynamics?

2. THREAT OF NEW ENTRANTS:
   - What are the barriers to entry?
   - Who are potential new entrants?
   - How does {company_name}'s position defend against new players?

3. BARGAINING POWER OF SUPPLIERS:
   - Who are the key suppliers?
   - What is the supplier concentration?
   - Are there switching costs or dependencies?

4. BARGAINING POWER OF BUYERS:
   - What are customer switching costs?
   - What drives customer loyalty?
   - What is the price sensitivity?

5. THREAT OF SUBSTITUTES:
   - What are the alternative solutions?
   - How strong is the substitute threat?
   - What drives substitution?

Return 4-5 bullet points on market attractiveness and {company_name}'s competitive positioning.
""",
    
    StrategicFramework.VALUE_CHAIN: """
Analyze {company_name}'s value chain and competitive advantages:

1. PRIMARY ACTIVITIES:
   - Inbound Logistics: Supply chain, sourcing
   - Operations: Manufacturing, production efficiency
   - Outbound Logistics: Distribution, delivery
   - Marketing & Sales: Brand, customer acquisition
   - Service: Customer support, after-sales

2. SUPPORT ACTIVITIES:
   - Firm Infrastructure: Management, systems
   - HR Management: Talent, culture
   - Technology Development: R&D, innovation
   - Procurement: Purchasing, partnerships

3. VALUE DRIVERS:
   - Where does {company_name} create the most value?
   - What are the unique capabilities?
   - Which activities drive competitive advantage?

4. COMPETITIVE MOATS:
   - What is difficult for competitors to replicate?
   - How sustainable are these advantages?

Return 4-5 bullet points on {company_name}'s key value drivers and competitive moats.
""",
    
    StrategicFramework.DUPONT_ANALYSIS: """
Conduct financial analysis for {company_name} using DuPont framework:

1. DUPONT ROE DECOMPOSITION:
   - Net Profit Margin: Profitability efficiency
   - Asset Turnover: Capital efficiency
   - Financial Leverage: Capital structure
   - ROE = Margin × Turnover × Leverage

2. PROFITABILITY ANALYSIS:
   - Operating margin trends
   - Gross margin vs peers
   - Cost structure efficiency

3. EFFICIENCY METRICS:
   - Asset utilization
   - Working capital management
   - Cash conversion cycle

4. CAPITAL STRUCTURE:
   - Debt levels and sustainability
   - Cost of capital
   - Financial flexibility

5. PEER COMPARISON:
   - How does {company_name} compare to industry?
   - What drives performance differences?

Return 4-5 bullet points on financial health and key performance drivers.
""",
    
    StrategicFramework.SWOT: """
Conduct SWOT analysis for {company_name}:

1. STRENGTHS (Internal, Positive):
   - What does {company_name} do well?
   - What unique resources/capabilities exist?
   - What competitive advantages are present?

2. WEAKNESSES (Internal, Negative):
   - What needs improvement?
   - What resource gaps exist?
   - Where are competitors stronger?

3. OPPORTUNITIES (External, Positive):
   - What market trends favor {company_name}?
   - What growth opportunities exist?
   - What partnerships or expansions make sense?

4. THREATS (External, Negative):
   - What market trends pose risks?
   - What competitive threats exist?
   - What regulatory or macro risks loom?

Return 4-5 bullet points on strategic positioning and priority actions.
""",
    
    StrategicFramework.ANSOFF_MATRIX: """
Analyze growth strategies for {company_name} using Ansoff Matrix:

1. MARKET PENETRATION (Existing Products, Existing Markets):
   - How can {company_name} increase market share?
   - What drives customer acquisition/retention?
   - What are the growth constraints?

2. MARKET DEVELOPMENT (Existing Products, New Markets):
   - What geographic expansion opportunities exist?
   - What new customer segments can be targeted?
   - What are the entry barriers?

3. PRODUCT DEVELOPMENT (New Products, Existing Markets):
   - What product innovations make sense?
   - What customer needs are unmet?
   - What is the development timeline?

4. DIVERSIFICATION (New Products, New Markets):
   - What adjacent markets are attractive?
   - What synergies exist?
   - What are the risks?

Return 4-5 bullet points on recommended growth strategies with risk assessment.
"""
}
