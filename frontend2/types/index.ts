// API Types
export interface QuestionRequest {
    company_name: string;
    industry?: string;
    question: string;
}

export interface Question {
    question: string;
    options: string[];
}

export interface QuestionResponse {
    questions: Question[];
}

export interface AnalysisRequest {
    company_name: string;
    industry?: string;
    question: string;
    include_mna?: boolean;
    output_format?: string[];
    question_answers?: Record<string, string>;
}

export interface AnalysisResponse {
    analysis_id: string;
    company_name: string;
    status: string;
    created_at: string;
    completed_at?: string;
    summary?: string;
    output_urls?: string[];
    execution_time?: number;
    errors?: string[];
}

// Analysis State (from backend)
export interface CompanyProfile {
    name: string;
    industry: string;
    key_facts: string[];
    ticker?: string;
    market_cap_billions?: number;
}

export interface MarketAnalysis {
    key_insights: string[];
}

export interface Competitor {
    name: string;
    key_point: string;
}

export interface FinancialModel {
    key_highlights: string[];
}

export interface Risk {
    risk: string;
    severity: string;
    description: string;
}

export interface RiskAssessment {
    top_risks: Risk[];
}

export interface StrategySynthesis {
    executive_summary: string;
    key_recommendations: string[];
    swot_summary: {
        top_strength: string;
        top_weakness: string;
        top_opportunity: string;
        top_threat: string;
    };
}

export interface AnalysisData {
    company_profile?: CompanyProfile;
    market_analysis?: MarketAnalysis;
    competitor_analysis?: Competitor[];
    financial_model?: FinancialModel;
    risk_assessment?: RiskAssessment;
    strategy_synthesis?: StrategySynthesis;
}
