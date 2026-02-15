import { AnalysisRequest, AnalysisResponse, QuestionRequest, QuestionResponse } from "@/types";
import { getToken } from "./auth";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Generic fetch wrapper with auth headers.
 */
async function fetchAPI<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const token = getToken();

    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        // Token expired or invalid — clear and redirect
        if (typeof window !== "undefined") {
            localStorage.removeItem("origin_labs_token");
            localStorage.removeItem("origin_labs_user");
            window.location.href = "/login";
        }
        throw new Error("Session expired. Please login again.");
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API Error: ${response.status}`);
    }

    return response.json();
}

// ==================== Auth API ====================

export interface LoginPayload {
    email: string;
    password: string;
}

export interface RegisterPayload {
    name: string;
    email: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    user: {
        id: string;
        name: string;
        email: string;
        created_at: string;
    };
}

export async function loginUser(payload: LoginPayload): Promise<TokenResponse> {
    return fetchAPI<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export async function registerUser(payload: RegisterPayload): Promise<TokenResponse> {
    return fetchAPI<TokenResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export async function getCurrentUser(): Promise<TokenResponse["user"]> {
    return fetchAPI<TokenResponse["user"]>("/auth/me");
}

// ==================== Chat API ====================

export interface ChatSession {
    id: string;
    title: string;
    company_name: string | null;
    preview: string;
    created_at: string;
    updated_at: string;
}

export interface ChatSessionDetail {
    id: string;
    title: string;
    company_name: string | null;
    industry: string | null;
    messages: Array<{
        id: string;
        role: string;
        content: string;
        timestamp: string;
    }>;
    created_at: string;
    updated_at: string;
}

export async function getChatSessions(): Promise<ChatSession[]> {
    return fetchAPI<ChatSession[]>("/chat/sessions");
}

export async function getChatSession(sessionId: string): Promise<ChatSessionDetail> {
    return fetchAPI<ChatSessionDetail>(`/chat/sessions/${sessionId}`);
}

export async function deleteChatSession(sessionId: string): Promise<void> {
    await fetchAPI(`/chat/sessions/${sessionId}`, { method: "DELETE" });
}

export async function updateSessionTitle(
    sessionId: string,
    title: string
): Promise<void> {
    await fetchAPI(`/chat/sessions/${sessionId}/title`, {
        method: "PUT",
        body: JSON.stringify({ title }),
    });
}

export async function sendChatMessage(payload: {
    session_id?: string;
    message: string;
    company_name?: string;
    industry?: string;
}): Promise<{
    session_id: string;
    message: string;
    action: string;
    ready_to_analyze: boolean;
}> {
    return fetchAPI("/chat", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

// ==================== Analysis API ====================

export async function fetchQuestions(payload: QuestionRequest): Promise<QuestionResponse> {
    return fetchAPI<QuestionResponse>("/analyze/questions", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export async function runAnalysis(payload: any): Promise<AnalysisResponse> {
    return fetchAPI<AnalysisResponse>("/chat/analyze", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

// ==================== Documents API ====================

export interface UploadedDocument {
    id: string;
    filename: string;
    pages: number;
    chunks: number;
    uploaded_at: string;
}

export async function uploadDocument(file: File): Promise<{
    message: string;
    document: UploadedDocument;
}> {
    const token = getToken();
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
    });

    if (response.status === 401) {
        if (typeof window !== "undefined") {
            localStorage.removeItem("origin_labs_token");
            window.location.href = "/login";
        }
        throw new Error("Session expired.");
    }

    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `Upload failed: ${response.status}`);
    }

    return response.json();
}

export async function getDocuments(): Promise<UploadedDocument[]> {
    return fetchAPI<UploadedDocument[]>("/documents");
}

export async function deleteDocument(docId: string): Promise<void> {
    await fetchAPI(`/documents/${docId}`, { method: "DELETE" });
}

// ==================== Comparison API ====================

export interface ComparisonRow {
    metric: string;
    [key: string]: string;  // company_0, company_1, etc.
}

export interface ComparisonCategory {
    name: string;
    rows: ComparisonRow[];
}

export interface ComparisonData {
    title: string;
    comparison_id: string;
    companies: string[];
    categories: ComparisonCategory[];
    verdict: string;
}

export interface ComparisonResult {
    comparison_id: string;
    comparison: ComparisonData;
    errors: string[];
}

export async function runComparison(payload: {
    session_id: string;
    companies: string[];
    industry?: string;
    chat_history: { role: string; content: string }[];
}): Promise<ComparisonResult> {
    return fetchAPI<ComparisonResult>("/chat/compare", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export async function downloadComparison(
    comparisonId: string,
    format: "pdf" | "ppt",
): Promise<{ download_url: string; filename: string }> {
    return fetchAPI("/chat/compare/download", {
        method: "POST",
        body: JSON.stringify({ comparison_id: comparisonId, format }),
    });
}

