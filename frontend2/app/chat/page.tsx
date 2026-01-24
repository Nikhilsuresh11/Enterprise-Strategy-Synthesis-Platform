"use client";

import { useState, useRef, useEffect } from "react";
import {
    Plus, Search, MessageSquare, FolderOpen, Clock,
    User, Send, Paperclip, Image as ImageIcon, RefreshCw
} from "lucide-react";

interface Message {
    id: string;
    role: string;
    content: string;
    timestamp: string;
}

const promptSuggestions = [
    {
        icon: "👤",
        title: "Investment Analysis",
        description: "Analyze a company for investment decision"
    },
    {
        icon: "📧",
        title: "Competitive Intelligence",
        description: "Research competitors and market position"
    },
    {
        icon: "📊",
        title: "Market Entry Strategy",
        description: "Evaluate new market opportunities"
    },
    {
        icon: "⚙️",
        title: "M&A Analysis",
        description: "Assess merger and acquisition targets"
    }
];

export default function ModernChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [isTyping, setIsTyping] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [showConfirmation, setShowConfirmation] = useState(false);
    const [companyName, setCompanyName] = useState("");
    const [industry, setIndustry] = useState("");
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [showPrompts, setShowPrompts] = useState(true);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isTyping]);

    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    const handleSend = async () => {
        if (!input.trim() || isTyping || isAnalyzing) return;

        setShowPrompts(false);

        const userMessage: Message = {
            id: Date.now().toString(),
            role: "user",
            content: input,
            timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsTyping(true);

        try {
            const response = await fetch("http://localhost:8000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: input,
                    company_name: companyName || undefined,
                    industry: industry || undefined,
                }),
            });

            const data = await response.json();

            if (!sessionId) {
                setSessionId(data.session_id);
            }

            // Extract company name
            if (!companyName) {
                const combinedText = (input + " " + data.message).toLowerCase();
                const patterns = [
                    /(?:analyze|analysis of|about|for)\s+([A-Z][a-zA-Z\s&]+?)(?:\s|$|,|\?)/,
                    /([A-Z][a-zA-Z\s&]+?)\s+(?:etf|stock|company|shares)/i,
                ];

                for (const pattern of patterns) {
                    const match = (input + " " + data.message).match(pattern);
                    if (match && match[1]) {
                        const extracted = match[1].trim();
                        if (extracted.length > 2 && extracted.length < 50) {
                            setCompanyName(extracted);
                            break;
                        }
                    }
                }
            }

            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: data.message,
                timestamp: new Date().toISOString(),
            };

            setMessages((prev) => [...prev, aiMessage]);

            if (data.ready_to_analyze) {
                setShowConfirmation(true);
            }
        } catch (error) {
            console.error("Chat error:", error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: "Sorry, I encountered an error. Please try again.",
                timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleStartAnalysis = async () => {
        setShowConfirmation(false);
        setIsAnalyzing(true);

        let finalCompanyName = companyName;
        if (!finalCompanyName) {
            const allText = messages.map(m => m.content).join(" ");
            const match = allText.match(/(?:analyze|analysis of|about)\s+([A-Z][a-zA-Z\s&]+?)(?:\s|$|,|\?)/);
            if (match && match[1]) {
                finalCompanyName = match[1].trim();
            } else {
                finalCompanyName = "Company";
            }
        }

        const analyzingMessage: Message = {
            id: Date.now().toString(),
            role: "assistant",
            content: `Perfect! Starting comprehensive MBB-grade analysis of ${finalCompanyName}. This will take 10-30 seconds...`,
            timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, analyzingMessage]);

        try {
            const response = await fetch("http://localhost:8000/chat/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    chat_history: messages.map((m) => ({
                        role: m.role,
                        content: m.content,
                        timestamp: m.timestamp,
                    })),
                    company_name: finalCompanyName,
                    industry: industry || undefined,
                    output_format: ["pdf", "ppt"],
                }),
            });

            const result = await response.json();
            setAnalysisResult(result);

            const completedMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: `✅ Analysis complete! Here's what I found about ${finalCompanyName}:`,
                timestamp: new Date().toISOString(),
            };

            setMessages((prev) => [...prev, completedMessage]);
        } catch (error) {
            console.error("Analysis error:", error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: "Sorry, the analysis failed. Please try again.",
                timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handlePromptClick = (prompt: typeof promptSuggestions[0]) => {
        setInput(prompt.description);
        inputRef.current?.focus();
    };

    return (
        <div className="flex h-screen bg-gray-50">
            {/* Left Sidebar */}
            <div className="w-16 bg-white border-r border-gray-200 flex flex-col items-center py-4 space-y-6">
                {/* Logo */}
                <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-lg">
                    S
                </div>

                {/* Navigation Icons */}
                <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                    <Plus className="w-5 h-5 text-gray-600" />
                </button>
                <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                    <Search className="w-5 h-5 text-gray-600" />
                </button>
                <button className="p-2 bg-purple-50 rounded-lg">
                    <MessageSquare className="w-5 h-5 text-purple-600" />
                </button>
                <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                    <FolderOpen className="w-5 h-5 text-gray-600" />
                </button>
                <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                    <Clock className="w-5 h-5 text-gray-600" />
                </button>

                {/* User Avatar at Bottom */}
                <div className="mt-auto">
                    <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                        <User className="w-5 h-5 text-gray-600" />
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col">
                {/* Chat Area */}
                <div className="flex-1 overflow-y-auto px-8 py-8">
                    <div className="max-w-3xl mx-auto">
                        {/* Welcome Screen */}
                        {showPrompts && messages.length === 0 && (
                            <div className="space-y-8">
                                <div className="text-center space-y-2">
                                    <h1 className="text-4xl font-semibold">
                                        Hi there, <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-indigo-600">Analyst</span>
                                    </h1>
                                    <h2 className="text-4xl font-semibold text-gray-800">
                                        What would <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-indigo-600">like to know?</span>
                                    </h2>
                                    <p className="text-gray-500 text-sm mt-4">
                                        Use one of the most common prompts below or use your own to begin
                                    </p>
                                </div>

                                {/* Prompt Cards */}
                                <div className="grid grid-cols-2 gap-4 mt-8">
                                    {promptSuggestions.map((prompt, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => handlePromptClick(prompt)}
                                            className="p-6 bg-white border border-gray-200 rounded-2xl hover:border-purple-300 hover:shadow-md transition-all text-left group"
                                        >
                                            <div className="text-2xl mb-3">{prompt.icon}</div>
                                            <h3 className="font-medium text-gray-900 mb-1 group-hover:text-purple-600 transition-colors">
                                                {prompt.title}
                                            </h3>
                                            <p className="text-sm text-gray-500">
                                                {prompt.description}
                                            </p>
                                        </button>
                                    ))}
                                </div>

                                <button className="flex items-center justify-center gap-2 text-gray-500 hover:text-purple-600 transition-colors mx-auto">
                                    <RefreshCw className="w-4 h-4" />
                                    <span className="text-sm">Refresh Prompts</span>
                                </button>
                            </div>
                        )}

                        {/* Messages */}
                        {messages.map((message) => (
                            <div
                                key={message.id}
                                className={`mb-6 ${message.role === "user" ? "flex justify-end" : ""}`}
                            >
                                <div
                                    className={`max-w-[80%] ${message.role === "user"
                                            ? "bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-3xl rounded-tr-sm"
                                            : "bg-white text-gray-800 rounded-3xl border border-gray-200"
                                        } px-6 py-4`}
                                >
                                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                                        {message.content}
                                    </p>
                                </div>
                            </div>
                        ))}

                        {/* Typing Indicator */}
                        {isTyping && (
                            <div className="mb-6">
                                <div className="bg-white rounded-3xl border border-gray-200 px-6 py-4 max-w-[80%]">
                                    <div className="flex space-x-2">
                                        <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                                        <div
                                            className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                                            style={{ animationDelay: "0.2s" }}
                                        ></div>
                                        <div
                                            className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                                            style={{ animationDelay: "0.4s" }}
                                        ></div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Analyzing Indicator */}
                        {isAnalyzing && (
                            <div className="flex justify-center mb-6">
                                <div className="bg-purple-50 border border-purple-200 rounded-2xl px-8 py-4">
                                    <div className="flex items-center space-x-3">
                                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600"></div>
                                        <span className="text-purple-800 font-medium">
                                            Running MBB-grade analysis...
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Confirmation Button */}
                        {showConfirmation && !isAnalyzing && (
                            <div className="flex justify-center mb-6">
                                <button
                                    onClick={handleStartAnalysis}
                                    className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-8 py-4 rounded-2xl font-semibold hover:shadow-lg transition-all"
                                >
                                    ✓ Yes, start the analysis!
                                </button>
                            </div>
                        )}

                        {/* Analysis Results */}
                        {analysisResult && (
                            <div className="bg-white rounded-3xl border border-gray-200 p-8 mt-6">
                                <h3 className="text-2xl font-bold mb-6 text-gray-900">
                                    Analysis Results
                                </h3>

                                {analysisResult.summary && (
                                    <div className="mb-6 p-6 bg-purple-50 rounded-2xl border border-purple-100">
                                        <h4 className="font-semibold mb-3 text-gray-800 text-lg">
                                            Executive Summary
                                        </h4>
                                        <p className="text-gray-700 leading-relaxed">
                                            {analysisResult.summary}
                                        </p>
                                    </div>
                                )}

                                {analysisResult.output_urls &&
                                    analysisResult.output_urls.length > 0 && (
                                        <div className="flex gap-4 flex-wrap mb-6">
                                            {analysisResult.output_urls.map((url: string, idx: number) => {
                                                const isPDF = url.endsWith('.pdf');
                                                const isPPT = url.endsWith('.pptx');

                                                return (
                                                    <a
                                                        key={idx}
                                                        href={`http://localhost:8000/download/${url}`}
                                                        download
                                                        className={`inline-flex items-center px-6 py-3 rounded-xl font-semibold transition-all ${isPDF
                                                                ? 'bg-red-600 hover:bg-red-700 text-white hover:shadow-lg'
                                                                : 'bg-orange-600 hover:bg-orange-700 text-white hover:shadow-lg'
                                                            }`}
                                                    >
                                                        {isPDF ? '📄 Download PDF Report' : '📊 Download Pitch Deck'}
                                                    </a>
                                                );
                                            })}
                                        </div>
                                    )}

                                <div className="text-sm text-gray-500">
                                    Completed in {analysisResult.execution_time?.toFixed(1)}s
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* Input Area */}
                <div className="border-t border-gray-200 bg-white px-8 py-6">
                    <div className="max-w-3xl mx-auto">
                        <div className="bg-white border border-gray-300 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                            <div className="flex items-end p-4">
                                <textarea
                                    ref={inputRef}
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    placeholder="Ask whatever you want..."
                                    disabled={isTyping || isAnalyzing}
                                    rows={1}
                                    className="flex-1 resize-none outline-none text-gray-800 placeholder-gray-400 disabled:bg-gray-50"
                                    style={{ maxHeight: "120px" }}
                                />
                                <div className="flex items-center gap-2 ml-4">
                                    <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                                        <Paperclip className="w-5 h-5 text-gray-500" />
                                    </button>
                                    <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                                        <ImageIcon className="w-5 h-5 text-gray-500" />
                                    </button>
                                    <button
                                        onClick={handleSend}
                                        disabled={!input.trim() || isTyping || isAnalyzing}
                                        className="p-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <Send className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                            <div className="px-4 pb-3 flex items-center justify-between text-xs text-gray-400">
                                <span>0/1000</span>
                                <span className="flex items-center gap-1">
                                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                                    All Web
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
