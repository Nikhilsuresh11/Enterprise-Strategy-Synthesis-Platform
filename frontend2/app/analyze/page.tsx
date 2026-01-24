"use client";

import { useState } from "react";
import { getQuestions, runAnalysis } from "@/lib/api";
import type {
    Question,
    AnalysisResponse,
    AnalysisData,
} from "@/types";

export default function AnalyzePage() {
    // Step management
    const [step, setStep] = useState<
        "initial" | "questions" | "analyzing" | "results"
    >("initial");

    // Form data
    const [companyName, setCompanyName] = useState("");
    const [industry, setIndustry] = useState("");
    const [userQuestion, setUserQuestion] = useState("");

    // Questions flow
    const [questions, setQuestions] = useState<Question[]>([]);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState<Record<string, string>>({});

    // Results
    const [analysisResponse, setAnalysisResponse] =
        useState<AnalysisResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Handle initial form submission
    const handleInitialSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        try {
            // Get clarifying questions
            const response = await getQuestions({
                company_name: companyName,
                industry: industry || undefined,
                question: userQuestion,
            });

            setQuestions(response.questions);
            setCurrentQuestionIndex(0);
            setStep("questions");
        } catch (err: any) {
            setError(err.message || "Failed to get questions");
        }
    };

    // Handle question answer
    const handleAnswer = (answer: string) => {
        const currentQuestion = questions[currentQuestionIndex];
        const newAnswers = {
            ...answers,
            [currentQuestion.question]: answer,
        };
        setAnswers(newAnswers);

        // Move to next question or start analysis
        if (currentQuestionIndex < questions.length - 1) {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
        } else {
            startAnalysis(newAnswers);
        }
    };

    // Skip questions and start analysis
    const handleSkip = () => {
        startAnalysis({});
    };

    // Start analysis
    const startAnalysis = async (questionAnswers: Record<string, string>) => {
        setStep("analyzing");
        setError(null);

        try {
            const response = await runAnalysis({
                company_name: companyName,
                industry: industry || undefined,
                question: userQuestion,
                question_answers: Object.keys(questionAnswers).length > 0 ? questionAnswers : undefined,
                output_format: ["json", "ppt"],
            });

            setAnalysisResponse(response);
            setStep("results");
        } catch (err: any) {
            setError(err.message || "Analysis failed");
            setStep("initial");
        }
    };

    // Reset and start new analysis
    const handleReset = () => {
        setStep("initial");
        setCompanyName("");
        setIndustry("");
        setUserQuestion("");
        setQuestions([]);
        setCurrentQuestionIndex(0);
        setAnswers({});
        setAnalysisResponse(null);
        setError(null);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
            <div className="container mx-auto px-4 py-12">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">
                        Enterprise Strategy Analysis
                    </h1>
                    <p className="text-gray-600">
                        AI-powered strategic insights for your business decisions
                    </p>
                </div>

                {/* Error Display */}
                {error && (
                    <div className="max-w-2xl mx-auto mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-red-800">{error}</p>
                    </div>
                )}

                {/* Step: Initial Form */}
                {step === "initial" && (
                    <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-lg p-8">
                        <h2 className="text-2xl font-semibold mb-6 text-gray-800">
                            Let's get started
                        </h2>
                        <form onSubmit={handleInitialSubmit} className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Company Name *
                                </label>
                                <input
                                    type="text"
                                    value={companyName}
                                    onChange={(e) => setCompanyName(e.target.value)}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="e.g., Tesla"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Industry (Optional)
                                </label>
                                <input
                                    type="text"
                                    value={industry}
                                    onChange={(e) => setIndustry(e.target.value)}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="e.g., Automotive"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Strategic Question *
                                </label>
                                <textarea
                                    value={userQuestion}
                                    onChange={(e) => setUserQuestion(e.target.value)}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="e.g., Should I invest in this company?"
                                    rows={4}
                                    required
                                />
                            </div>

                            <button
                                type="submit"
                                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                            >
                                Get Started →
                            </button>
                        </form>
                    </div>
                )}

                {/* Step: Questions (One at a time) */}
                {step === "questions" && questions.length > 0 && (
                    <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-lg p-8">
                        <div className="mb-6">
                            <div className="flex justify-between items-center mb-4">
                                <span className="text-sm text-gray-500">
                                    Question {currentQuestionIndex + 1} of {questions.length}
                                </span>
                                <button
                                    onClick={handleSkip}
                                    className="text-sm text-gray-500 hover:text-gray-700"
                                >
                                    Skip questions →
                                </button>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-blue-600 h-2 rounded-full transition-all"
                                    style={{
                                        width: `${((currentQuestionIndex + 1) / questions.length) * 100}%`,
                                    }}
                                />
                            </div>
                        </div>

                        <h2 className="text-2xl font-semibold mb-6 text-gray-800">
                            {questions[currentQuestionIndex].question}
                        </h2>

                        <div className="space-y-3">
                            {questions[currentQuestionIndex].options.map((option, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => handleAnswer(option)}
                                    className="w-full text-left px-6 py-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all"
                                >
                                    {option}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Step: Analyzing */}
                {step === "analyzing" && (
                    <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-lg p-12 text-center">
                        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-6"></div>
                        <h2 className="text-2xl font-semibold mb-2 text-gray-800">
                            Analyzing {companyName}...
                        </h2>
                        <p className="text-gray-600">
                            Our AI agents are gathering insights. This may take 10-30 seconds.
                        </p>
                    </div>
                )}

                {/* Step: Results */}
                {step === "results" && analysisResponse && (
                    <div className="max-w-5xl mx-auto">
                        <div className="bg-white rounded-xl shadow-lg p-8 mb-6">
                            <div className="flex justify-between items-start mb-6">
                                <div>
                                    <h2 className="text-3xl font-bold text-gray-900 mb-2">
                                        {companyName} Analysis
                                    </h2>
                                    <p className="text-gray-600">
                                        Completed in {analysisResponse.execution_time?.toFixed(1)}s
                                    </p>
                                </div>
                                <button
                                    onClick={handleReset}
                                    className="px-4 py-2 text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50"
                                >
                                    New Analysis
                                </button>
                            </div>

                            {/* Executive Summary */}
                            {analysisResponse.summary && (
                                <div className="mb-8 p-6 bg-blue-50 rounded-lg">
                                    <h3 className="text-lg font-semibold mb-3 text-gray-800">
                                        Executive Summary
                                    </h3>
                                    <p className="text-gray-700 leading-relaxed">
                                        {analysisResponse.summary}
                                    </p>
                                </div>
                            )}

                            {/* Download Deck */}
                            {analysisResponse.output_urls && analysisResponse.output_urls.length > 0 && (
                                <div className="mb-6">
                                    <a
                                        href={`http://localhost:8000/download/${analysisResponse.output_urls[0]}`}
                                        download
                                        className="inline-flex items-center px-6 py-3 bg-orange-600 text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors"
                                    >
                                        📥 Download Pitch Deck
                                    </a>
                                </div>
                            )}

                            {/* Placeholder for detailed results */}
                            <div className="text-center py-12 text-gray-500">
                                <p>Detailed analysis tabs will be displayed here</p>
                                <p className="text-sm mt-2">
                                    (Company Overview, Market, Financial, Risks, Strategy, SWOT)
                                </p>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
