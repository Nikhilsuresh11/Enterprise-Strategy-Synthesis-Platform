"""RAG corpus ingestion script - generates and uploads sample data to Pinecone."""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.services.rag_service import RAGService
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Sample case studies data
CASE_STUDIES = [
    {
        "title": "Zomato's Market Expansion into UAE",
        "industry": "Food Delivery",
        "region": "Middle East",
        "date": "2023-08-15",
        "text": """Zomato successfully expanded into the UAE food delivery market, achieving 15% market share within 12 months. The strategy involved a phased rollout starting with Dubai, focusing on premium positioning to differentiate from Talabat's mass-market approach. Total investment of $50M over 18 months resulted in $8M monthly GMV by month 12. Key success factors included superior technology (15-min delivery), restaurant-friendly commission structure (15% vs 25% industry standard), and localized menu curation. The company overcame challenges including regulatory compliance, Ramadan operational spikes, and extreme weather logistics. Break-even projected at month 24.""",
        "source": "Zomato UAE Expansion Case Study",
        "credibility_score": 0.95
    },
    {
        "title": "Flipkart Grocery Expansion Strategy",
        "industry": "E-commerce",
        "region": "India",
        "date": "2023-06-20",
        "text": """Flipkart's grocery vertical expansion across 15 Indian cities demonstrated a hub-and-spoke distribution model. Investment of ₹500 crore enabled dark store network of 50 locations, achieving 2-hour delivery in metro cities. Market share grew from 8% to 18% in 18 months, competing against BigBasket (35%) and Amazon Fresh (22%). Unit economics improved with basket size increasing from ₹850 to ₹1,200 through cross-category bundling. Key learnings include importance of fresh produce quality control, hyperlocal inventory management, and integration with existing logistics network.""",
        "source": "Flipkart Grocery Case Study",
        "credibility_score": 0.90
    },
    {
        "title": "Paytm International Expansion Analysis",
        "industry": "Fintech",
        "region": "Southeast Asia",
        "date": "2023-05-10",
        "text": """Paytm's expansion into Bangladesh and Nepal markets through strategic partnerships with local banks and telecom operators. Total investment of $30M focused on digital wallet and QR code payment infrastructure. Achieved 2M active users in 12 months with 40% month-over-month transaction growth. Regulatory navigation was critical, requiring 6 months for banking licenses. The strategy emphasized agent network development (5,000 agents) and merchant onboarding (50,000 merchants). Key challenge was low smartphone penetration requiring USSD-based solutions.""",
        "source": "Paytm International Case Study",
        "credibility_score": 0.88
    },
    {
        "title": "Ola Electric Vehicle Rollout",
        "industry": "Automotive",
        "region": "India",
        "date": "2023-09-01",
        "text": """Ola Electric's nationwide scooter rollout strategy involved building 500 experience centers and establishing battery-swapping infrastructure across 100 cities. Investment of ₹2,400 crore in manufacturing (Futurefactory) enabled 2M annual production capacity. Market penetration achieved 25% in electric two-wheeler segment within 18 months. Pricing strategy positioned at ₹1.1L, undercutting competitors by 15%. Challenges included battery supply chain constraints, charging infrastructure development, and after-sales service network establishment. Customer acquisition cost of ₹8,000 with 35% coming from direct online sales.""",
        "source": "Ola Electric Case Study",
        "credibility_score": 0.92
    },
    {
        "title": "Swiggy Instamart City Expansion",
        "industry": "Quick Commerce",
        "region": "India",
        "date": "2023-07-25",
        "text": """Swiggy Instamart's expansion from 10 to 30 cities demonstrated quick commerce scalability. Dark store density strategy with 3-5 stores per city enabled 15-minute delivery promise. Investment of ₹800 crore supported infrastructure and customer acquisition. Average order value of ₹450 with 4.5 orders per customer monthly. Competition with Blinkit (Zomato) and Zepto intensified, requiring aggressive discounting (20% average). Key success metrics: 85% on-time delivery, 92% customer satisfaction, and 30% repeat rate. Operational challenges included inventory forecasting for 2,500 SKUs and managing perishables wastage (8%).""",
        "source": "Swiggy Instamart Case Study",
        "credibility_score": 0.91
    },
    {
        "title": "Walmart-Flipkart Acquisition Analysis",
        "industry": "E-commerce M&A",
        "region": "India",
        "date": "2023-04-15",
        "text": """Walmart's $16B acquisition of 77% stake in Flipkart represented largest e-commerce M&A in India. Strategic rationale included access to 300M+ Indian consumers and competition with Amazon India. Due diligence revealed $7.5B annual GMV, 150M registered users, and market leadership in fashion and electronics. Post-acquisition integration focused on supply chain optimization, leveraging Walmart's global sourcing, and PhonePe fintech synergies. Regulatory challenges included FDI compliance and marketplace model restrictions. Three-year post-acquisition performance showed GMV growth to $12B, though profitability remained elusive with $1.5B annual losses.""",
        "source": "Walmart-Flipkart M&A Case Study",
        "credibility_score": 0.94
    },
    {
        "title": "Tata-BigBasket Merger Evaluation",
        "industry": "Grocery M&A",
        "region": "India",
        "date": "2023-03-20",
        "text": """Tata Digital's acquisition of 64% stake in BigBasket for $1.2B created India's largest omnichannel grocery platform. Strategic fit included integration with Tata Neu super-app and leveraging Tata's retail infrastructure (Westside, Croma stores). BigBasket brought 10M active customers, 25,000 products, and presence in 300+ cities. Synergy opportunities identified: ₹200 crore annual savings through Tata supply chain, cross-selling to Tata customer base (100M+ users), and private label development. Integration challenges included technology platform consolidation and organizational culture alignment. Projected break-even timeline: 24 months post-acquisition.""",
        "source": "Tata-BigBasket M&A Case Study",
        "credibility_score": 0.89
    },
    {
        "title": "Reliance-JioMart Integration Strategy",
        "industry": "Retail Integration",
        "region": "India",
        "date": "2023-02-10",
        "text": """Reliance's integration of JioMart with 12,000 Reliance Retail stores created unique O2O (online-to-offline) model. Investment of ₹5,000 crore in technology and logistics enabled hyperlocal delivery from nearby stores. WhatsApp commerce integration reached 50M users, leveraging Jio's 400M subscriber base. Key differentiator: 2-hour delivery using existing store inventory, eliminating dark store costs. Performance metrics: ₹3,000 crore monthly GMV, 15M monthly active users, average basket size ₹1,800. Challenges included inventory synchronization across channels, training 100,000+ store staff, and managing customer expectations for product availability.""",
        "source": "Reliance-JioMart Case Study",
        "credibility_score": 0.93
    },
    {
        "title": "EdTech Startup Investment Decision - Unacademy",
        "industry": "EdTech Investment",
        "region": "India",
        "date": "2023-01-15",
        "text": """Investment evaluation of Unacademy's Series H round ($150M at $3.4B valuation). Market analysis showed Indian EdTech TAM of $10B growing at 25% CAGR. Unacademy metrics: 50M registered users, 10M monthly active learners, 60,000 educators, and presence in test prep, K-12, and upskilling segments. Unit economics: $15 CAC, $120 LTV, 8-month payback period. Competitive landscape: BYJU'S ($22B valuation), PhysicsWallah (bootstrapped), and Khan Academy (free). Investment thesis centered on category leadership in test prep (60% market share), strong brand recall, and path to profitability (projected 18 months). Risk factors: regulatory uncertainty, customer acquisition costs, and retention challenges (65% annual retention).""",
        "source": "Unacademy Investment Analysis",
        "credibility_score": 0.87
    },
    {
        "title": "HealthTech Platform Funding Analysis - Practo",
        "industry": "HealthTech Investment",
        "region": "India",
        "date": "2022-12-20",
        "text": """Practo's Series F funding evaluation ($100M at $1.8B valuation) for expanding telemedicine and diagnostic services. Platform metrics: 30M monthly users, 100,000 verified doctors, presence in 50 cities. Revenue model: consultation fees (20% take rate), diagnostic commissions (15%), and SaaS subscriptions for clinics (₹5,000/month). Market opportunity: Indian healthcare market $280B with 3% digital penetration. Competitive analysis: Apollo 24/7, Tata 1mg, PharmEasy. Investment highlights: strong network effects, high switching costs for doctors, and integration with diagnostic labs (2,000 partners). Concerns: regulatory compliance, insurance integration complexity, and customer acquisition costs (₹450 per user).""",
        "source": "Practo Investment Analysis",
        "credibility_score": 0.86
    }
]

# Industry reports data
INDUSTRY_REPORTS = [
    {
        "title": "Food Delivery Market Overview - India & Middle East",
        "industry": "Food Delivery",
        "region": "India, Middle East",
        "date": "2023-09-01",
        "text": """The food delivery market in India and Middle East represents combined TAM of $15B with 18% CAGR through 2027. India market ($12B) dominated by Zomato (45%), Swiggy (42%), and others (13%). Middle East market ($3B) led by Talabat (55%), Deliveroo (20%), and emerging players (25%). Key trends: cloud kitchens growing 35% annually, quick commerce integration, and subscription models (Zomato Gold, Swiggy One). Average order values: India ₹350, UAE AED 85. Commission structures: 18-25% from restaurants, 15-20% from cloud kitchens. Customer acquisition costs declining due to market maturity: India ₹120, UAE AED 35. Regulatory landscape includes food safety compliance, delivery partner classification, and data localization requirements.""",
        "source": "McKinsey Food Delivery Report 2023",
        "credibility_score": 0.96
    },
    {
        "title": "Fintech in India - Market Landscape 2023",
        "industry": "Fintech",
        "region": "India",
        "date": "2023-08-15",
        "text": """Indian fintech market valued at $150B with 22% CAGR, driven by UPI adoption (10B monthly transactions), digital lending growth, and wealth-tech emergence. Segment breakdown: Payments (45%), Lending (30%), Wealth Management (15%), Insurance (10%). Key players: Paytm (payments), PhonePe (UPI leader with 48% share), CRED (credit cards), and Zerodha (stock broking). Regulatory environment includes RBI digital lending guidelines, account aggregator framework, and CBDC pilot. Investment trends: $8B deployed in 2023 across 450 deals. Unit economics improving with payment companies achieving 15-20% EBITDA margins. Challenges: customer acquisition costs ($8-12), regulatory compliance, and competition from traditional banks' digital initiatives.""",
        "source": "KPMG India Fintech Report 2023",
        "credibility_score": 0.95
    },
    {
        "title": "E-commerce Logistics - Infrastructure and Challenges",
        "industry": "Logistics",
        "region": "India",
        "date": "2023-07-20",
        "text": """E-commerce logistics market in India growing at 25% CAGR to reach $15B by 2025. Infrastructure includes 2,500 fulfillment centers, 50,000 delivery hubs, and 500,000 delivery personnel. Key players: Delhivery (25% market share), Ecom Express (18%), Blue Dart (15%), and captive arms (Amazon, Flipkart). Technology adoption: route optimization (95% of top players), automated sorting (60% of warehouses), and drone delivery pilots. Cost structure: last-mile delivery represents 55% of total logistics cost. Challenges include tier-2/3 city penetration, reverse logistics (30% of fashion orders), and seasonal demand spikes (festive season 3x normal volume). Sustainability initiatives: EV fleet adoption (15% of vehicles), packaging reduction, and carbon-neutral delivery options.""",
        "source": "Deloitte Logistics Report 2023",
        "credibility_score": 0.94
    },
    {
        "title": "EdTech Landscape - Growth Drivers and Opportunities",
        "industry": "EdTech",
        "region": "India",
        "date": "2023-06-10",
        "text": """Indian EdTech market projected to reach $10B by 2025 (30% CAGR) driven by test preparation demand, K-12 digitization, and upskilling needs. Segment analysis: Test Prep (40% market share, $4B), K-12 (35%, $3.5B), Higher Education (15%, $1.5B), Upskilling (10%, $1B). Major players: BYJU'S (8M paid subscribers), Unacademy (test prep leader), PhysicsWallah (affordable segment), and Coursera (professional courses). Business models: subscription (60% revenue), one-time purchases (25%), freemium (15%). User metrics: 180M registered learners, 35M paying customers, average subscription ₹15,000 annually. Challenges: high customer acquisition costs (₹3,000-5,000), 60-65% annual retention, and regulatory scrutiny on aggressive sales practices. Opportunities: vernacular content (growing 40% YoY), AI-powered personalization, and corporate upskilling partnerships.""",
        "source": "BCG EdTech Report 2023",
        "credibility_score": 0.93
    },
    {
        "title": "Healthcare Technology - Digital Health Adoption",
        "industry": "HealthTech",
        "region": "India",
        "date": "2023-05-15",
        "text": """Indian HealthTech market growing at 35% CAGR to reach $21B by 2025, accelerated by COVID-19 digital adoption. Segments: Telemedicine (30% share), E-Pharmacy (40%), Diagnostics (20%), Fitness/Wellness (10%). Leading platforms: Practo (30M users), Apollo 24/7, Tata 1mg (e-pharmacy leader with 35% market share), and PharmEasy. Regulatory framework: telemedicine guidelines, online pharmacy regulations, and data privacy (Digital Personal Data Protection Act). Technology trends: AI diagnostics (accuracy 85-90%), remote patient monitoring, and blockchain for medical records. Business metrics: average consultation fee ₹300-500, e-pharmacy basket size ₹800, diagnostic commission 15-20%. Challenges: doctor onboarding (trust and adoption), insurance integration, last-mile delivery for medicines, and quality control. Government initiatives: Ayushman Bharat Digital Mission creating unified health ID for 1.3B citizens.""",
        "source": "EY HealthTech Report 2023",
        "credibility_score": 0.92
    }
]

# Financial templates data
FINANCIAL_TEMPLATES = [
    {
        "title": "TAM/SAM/SOM Calculation Methodology",
        "industry": "General",
        "region": "Global",
        "date": "2023-10-01",
        "text": """Total Addressable Market (TAM), Serviceable Available Market (SAM), and Serviceable Obtainable Market (SOM) framework for market sizing. TAM represents total market demand for a product/service, calculated using top-down (industry reports) or bottom-up (unit economics) approaches. Example: Food delivery TAM in India = (Urban population 400M) × (Ordering frequency 2x/month) × (Average order value ₹350) × (12 months) = ₹3.36T annually. SAM narrows to addressable segment based on geography, demographics, or product fit. Example: Metro cities only = 150M population = ₹1.26T. SOM represents realistic market share achievable in 3-5 years based on competition, resources, and go-to-market strategy. Example: Targeting 10% share = ₹126B. Validation methods: compare with competitor revenues, industry benchmarks, and historical penetration rates. Common pitfalls: overestimating willingness to pay, ignoring competitive dynamics, and unrealistic conversion assumptions.""",
        "source": "McKinsey Market Sizing Framework",
        "credibility_score": 0.98
    },
    {
        "title": "DCF Valuation Template - Discounted Cash Flow",
        "industry": "General",
        "region": "Global",
        "date": "2023-09-15",
        "text": """Discounted Cash Flow (DCF) valuation methodology for estimating intrinsic company value. Steps: (1) Project free cash flows for 5-10 years based on revenue growth, EBITDA margins, capex, and working capital changes. (2) Calculate terminal value using perpetuity growth method: TV = FCF(final year) × (1+g) / (WACC-g), where g = long-term growth rate (2-3%). (3) Discount all cash flows to present value using WACC (Weighted Average Cost of Capital). WACC calculation: WACC = (E/V × Re) + (D/V × Rd × (1-Tc)), where E=equity value, D=debt, V=total value, Re=cost of equity (CAPM), Rd=cost of debt, Tc=tax rate. (4) Sum discounted cash flows and terminal value. (5) Sensitivity analysis varying WACC (±2%) and growth rate (±1%). Example: SaaS company with $100M revenue, 30% growth, 20% EBITDA margin, WACC 12%, terminal growth 3% yields valuation of $800M-1.2B depending on assumptions. Key considerations: revenue quality, margin sustainability, and competitive moat.""",
        "source": "Investment Banking Valuation Guide",
        "credibility_score": 0.97
    },
    {
        "title": "Unit Economics Framework - CAC, LTV, Payback",
        "industry": "General",
        "region": "Global",
        "date": "2023-08-20",
        "text": """Unit economics framework for evaluating business model sustainability. Key metrics: (1) Customer Acquisition Cost (CAC) = Total marketing & sales spend / New customers acquired. Include all channels: paid ads, sales team, partnerships. (2) Lifetime Value (LTV) = Average revenue per user × Gross margin % × Average customer lifetime. For subscription: LTV = ARPU × Gross margin / Churn rate. (3) LTV:CAC ratio - healthy businesses maintain 3:1 or higher. (4) Payback period = CAC / (Monthly recurring revenue × Gross margin). Target < 12 months for sustainable growth. Example: SaaS company with $500 CAC, $100 monthly subscription, 80% gross margin, 5% monthly churn yields LTV = $100 × 0.8 / 0.05 = $1,600, LTV:CAC = 3.2:1, Payback = 6.25 months. Cohort analysis essential: track metrics by acquisition month to identify trends. Red flags: increasing CAC, declining LTV, extending payback periods. Optimization levers: improve conversion rates, reduce churn, increase pricing, expand to higher-value segments.""",
        "source": "a16z Unit Economics Guide",
        "credibility_score": 0.96
    },
    {
        "title": "Market Sizing Approach - Top-Down vs Bottom-Up",
        "industry": "General",
        "region": "Global",
        "date": "2023-07-25",
        "text": """Market sizing methodologies for estimating market opportunity. Top-Down approach: Start with macro data (industry reports, government statistics) and apply filters. Example: Indian e-commerce market $100B × Fashion category 30% × Premium segment 20% = $6B TAM. Advantages: quick, uses credible sources. Disadvantages: may miss nuances, relies on external data accuracy. Bottom-Up approach: Build from micro-level unit economics. Example: Target customer segment 50M × Purchase frequency 4x/year × Average transaction ₹2,000 = ₹400B. Advantages: grounded in business reality, validates assumptions. Disadvantages: time-intensive, requires detailed data. Best practice: Use both methods and triangulate. Validate with: (1) Competitor revenues (sum of top 3-5 players should be 60-80% of market), (2) Adjacent market comparisons (e-commerce penetration in similar economies), (3) Expert interviews (industry participants, analysts). Common errors: double-counting, ignoring cannibalization, unrealistic penetration rates. Always sanity-check: Does the number pass the smell test?"""
,
        "source": "Bain Market Sizing Methodology",
        "credibility_score": 0.95
    },
    {
        "title": "Competitive Analysis Framework - Porter's Five Forces",
        "industry": "General",
        "region": "Global",
        "date": "2023-06-30",
        "text": """Porter's Five Forces framework for analyzing competitive intensity and industry attractiveness. (1) Threat of New Entrants: Assess barriers to entry including capital requirements, economies of scale, brand loyalty, regulatory hurdles, and access to distribution. High barriers = attractive industry. Example: Food delivery has low barriers (asset-light model) leading to intense competition. (2) Bargaining Power of Suppliers: Evaluate supplier concentration, switching costs, and differentiation. Example: Cloud kitchens have low power as restaurants can easily switch platforms. (3) Bargaining Power of Buyers: Consider buyer concentration, price sensitivity, and switching costs. Example: Food delivery customers have high power due to low switching costs and price comparison ease. (4) Threat of Substitutes: Identify alternative solutions and their price-performance trade-offs. Example: Home cooking, dining out, meal kits substitute food delivery. (5) Competitive Rivalry: Analyze number of competitors, industry growth rate, and exit barriers. Example: Food delivery shows intense rivalry (Zomato vs Swiggy) with high marketing spend. Synthesis: Combine forces to determine industry profitability potential and strategic positioning opportunities. Use to inform pricing strategy, differentiation approach, and investment decisions.""",
        "source": "Harvard Business Review - Porter Framework",
        "credibility_score": 0.99
    }
]


async def ingest_all_data():
    """Ingest all sample data into Pinecone."""
    settings = get_settings()
    
    print("\n" + "="*60)
    print("RAG Corpus Ingestion - Stratagem AI")
    print("="*60 + "\n")
    
    # Initialize RAG service
    print("Initializing RAG service...")
    rag = RAGService(
        api_key=settings.pinecone_api_key,
        environment=settings.pinecone_environment,
        index_name=settings.pinecone_index_name,
        embedding_model=settings.embedding_model
    )
    
    await rag.connect()
    print("✅ Connected to Pinecone\n")
    
    # Ingest case studies
    print(f"Ingesting {len(CASE_STUDIES)} case studies...")
    case_study_docs = [
        {
            "text": doc["text"],
            "metadata": {
                "source": doc["source"],
                "source_type": "case_study",
                "industry": doc["industry"],
                "region": doc["region"],
                "date": doc["date"],
                "credibility_score": doc["credibility_score"],
                "title": doc["title"]
            }
        }
        for doc in CASE_STUDIES
    ]
    
    result = await rag.upsert_documents(case_study_docs, namespace="case_studies")
    print(f"✅ Case studies: {result['inserted']} inserted, {result['failed']} failed\n")
    
    # Ingest industry reports
    print(f"Ingesting {len(INDUSTRY_REPORTS)} industry reports...")
    report_docs = [
        {
            "text": doc["text"],
            "metadata": {
                "source": doc["source"],
                "source_type": "industry_report",
                "industry": doc["industry"],
                "region": doc["region"],
                "date": doc["date"],
                "credibility_score": doc["credibility_score"],
                "title": doc["title"]
            }
        }
        for doc in INDUSTRY_REPORTS
    ]
    
    result = await rag.upsert_documents(report_docs, namespace="industry_reports")
    print(f"✅ Industry reports: {result['inserted']} inserted, {result['failed']} failed\n")
    
    # Ingest financial templates
    print(f"Ingesting {len(FINANCIAL_TEMPLATES)} financial templates...")
    template_docs = [
        {
            "text": doc["text"],
            "metadata": {
                "source": doc["source"],
                "source_type": "financial_template",
                "industry": doc["industry"],
                "region": doc["region"],
                "date": doc["date"],
                "credibility_score": doc["credibility_score"],
                "title": doc["title"]
            }
        }
        for doc in FINANCIAL_TEMPLATES
    ]
    
    result = await rag.upsert_documents(template_docs, namespace="financial_templates")
    print(f"✅ Financial templates: {result['inserted']} inserted, {result['failed']} failed\n")
    
    # Summary
    total_docs = len(CASE_STUDIES) + len(INDUSTRY_REPORTS) + len(FINANCIAL_TEMPLATES)
    print("="*60)
    print(f"✅ Ingestion Complete!")
    print(f"   Total documents: {total_docs}")
    print(f"   Namespaces: case_studies, industry_reports, financial_templates")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(ingest_all_data())
