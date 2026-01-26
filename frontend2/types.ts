// Type definitions for API requests and responses

export interface Question {
    id: string;
    question: string;
    text: string;
    category: string;
    options: string[];
}

export interface QuestionRequest {
    company_name: string;
    industry?: string;
    question?: string;
}

export interface QuestionResponse {
    questions: Question[];
    session_id: string;
}

export interface AnalysisRequest {
    company_name: string;
    industry?: string;
    question?: string;
    answers?: Record<string, string>;
    question_answers?: Record<string, string>;
    session_id?: string;
    output_format?: string[];
}

export interface AnalysisResponse {
    session_id: string;
    status: string;
    company_profile?: any;
    market_analysis?: any;
    financial_model?: any;
    risk_assessment?: any;
    strategy_synthesis?: any;
    validation?: any;
    output_urls?: string[];
    pitch_deck_path?: string;
    error?: string;
    execution_time?: number;
    summary?: string;
}

export interface ChatMessage {
    role: "user" | "assistant";
    content: string;
}

export interface ChatRequest {
    session_id: string;
    message: string;
    chat_history?: ChatMessage[];
}

export interface ChatResponse {
    session_id: string;
    message: string;
    action: "continue" | "ready_to_analyze";
    ready_to_analyze: boolean;
}
