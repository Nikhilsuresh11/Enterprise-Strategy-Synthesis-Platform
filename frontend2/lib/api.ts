import type {
    QuestionRequest,
    QuestionResponse,
    AnalysisRequest,
    AnalysisResponse,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class APIError extends Error {
    constructor(
        message: string,
        public status?: number,
        public data?: any
    ) {
        super(message);
        this.name = "APIError";
    }
}

async function fetchAPI<T>(
    endpoint: string,
    options?: RequestInit
): Promise<T> {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                "Content-Type": "application/json",
                ...options?.headers,
            },
            ...options,
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new APIError(
                errorData.detail || `API Error: ${response.statusText}`,
                response.status,
                errorData
            );
        }

        return await response.json();
    } catch (error) {
        if (error instanceof APIError) {
            throw error;
        }
        throw new APIError(
            error instanceof Error ? error.message : "Network error occurred"
        );
    }
}

/**
 * Get clarifying questions for a company analysis
 */
export async function getQuestions(
    request: QuestionRequest
): Promise<QuestionResponse> {
    return fetchAPI<QuestionResponse>("/analyze/questions", {
        method: "POST",
        body: JSON.stringify(request),
    });
}

/**
 * Run company analysis
 */
export async function runAnalysis(
    request: AnalysisRequest
): Promise<AnalysisResponse> {
    return fetchAPI<AnalysisResponse>("/analyze", {
        method: "POST",
        body: JSON.stringify(request),
    });
}

/**
 * Download pitch deck (if available)
 */
export function downloadDeck(deckPath: string): void {
    // Create a link and trigger download
    const link = document.createElement("a");
    link.href = `${API_BASE_URL}/download/${encodeURIComponent(deckPath)}`;
    link.download = deckPath.split("/").pop() || "pitch_deck.pptx";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
