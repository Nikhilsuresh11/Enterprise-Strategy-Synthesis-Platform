"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send, Sparkles, ArrowDown, RefreshCw, Paperclip, X, FileText, Loader2, Download
} from "lucide-react";
import {
  sendChatMessage, getChatSession, runAnalysis, API_BASE_URL,
  uploadDocument, getDocuments, deleteDocument,
  runComparison, downloadComparison,
  type UploadedDocument,
  type ComparisonResult,
  type ComparisonData,
} from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";

interface Message {
  id: string;
  role: string;
  content: string;
  timestamp: string;
}

const promptSuggestions = [
  { icon: "📊", title: "Investment Analysis", description: "Analyze a company for investment decision" },
  { icon: "🏢", title: "Competitive Intelligence", description: "Research competitors and market position" },
  { icon: "🌍", title: "Market Entry Strategy", description: "Evaluate new market opportunities" },
  { icon: "🤝", title: "M&A Analysis", description: "Assess merger and acquisition targets" },
];

export default function ChatPage() {
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
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDocument[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [comparisonResult, setComparisonResult] = useState<ComparisonData | null>(null);
  const [comparisonId, setComparisonId] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { user, isLoading } = useAuth();

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 200) + "px";
    }
  }, [input]);

  // Load user's uploaded documents
  useEffect(() => {
    const loadDocs = async () => {
      try {
        const docs = await getDocuments();
        setUploadedDocs(docs);
      } catch { }
    };
    if (user) loadDocs();
  }, [user]);

  // ==================== File Upload ====================

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Only PDF files are supported.");
      setTimeout(() => setUploadError(""), 4000);
      return;
    }

    setIsUploading(true);
    setUploadError("");

    try {
      const result = await uploadDocument(file);
      setUploadedDocs((prev) => [result.document, ...prev]);

      const sysMsg: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: `📄 **${file.name}** uploaded successfully (${result.document.pages} pages, ${result.document.chunks} chunks indexed). You can now ask questions about this document.`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, sysMsg]);
      setShowPrompts(false);
    } catch (err: any) {
      setUploadError(err.message || "Upload failed.");
      setTimeout(() => setUploadError(""), 4000);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDeleteDoc = async (docId: string) => {
    try {
      await deleteDocument(docId);
      setUploadedDocs((prev) => prev.filter((d) => d.id !== docId));
    } catch { }
  };

  // ==================== Sidebar Event Listeners ====================

  const loadSession = useCallback(async (sid: string) => {
    try {
      const session = await getChatSession(sid);
      setSessionId(session.id);
      setMessages(
        session.messages.map((m: any) => ({
          id: m.id || Date.now().toString(),
          role: m.role,
          content: m.content,
          timestamp: m.timestamp || new Date().toISOString(),
        }))
      );
      setCompanyName(session.company_name || "");
      setIndustry(session.industry || "");
      setShowPrompts(false);
      setAnalysisResult(null);
      setShowConfirmation(false);
    } catch {
      // Session might have been deleted
    }
  }, []);

  const resetChat = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setInput("");
    setCompanyName("");
    setIndustry("");
    setShowPrompts(true);
    setAnalysisResult(null);
    setShowConfirmation(false);
    setIsTyping(false);
    setIsAnalyzing(false);
  }, []);

  useEffect(() => {
    const handleSelectSession = (e: Event) => {
      const { sessionId: sid } = (e as CustomEvent).detail;
      loadSession(sid);
    };

    const handleNewChat = () => {
      resetChat();
    };

    window.addEventListener("sidebar:selectSession", handleSelectSession);
    window.addEventListener("sidebar:newChat", handleNewChat);
    return () => {
      window.removeEventListener("sidebar:selectSession", handleSelectSession);
      window.removeEventListener("sidebar:newChat", handleNewChat);
    };
  }, [loadSession, resetChat]);

  // ==================== Send Message ====================

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);
    setShowPrompts(false);

    try {
      const data = await sendChatMessage({
        session_id: sessionId || undefined,
        message: userMessage.content,
        company_name: companyName || undefined,
        industry: industry || undefined,
      });

      // If this is a new session, update sidebar
      if (!sessionId) {
        setSessionId(data.session_id);
        window.dispatchEvent(
          new CustomEvent("chat:sessionUpdated", {
            detail: { sessionId: data.session_id },
          })
        );
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMessage]);

      // Use backend-detected companies if available
      if (data.companies && data.companies.length > 0) {
        if (data.analysis_type === "comparison" && data.companies.length >= 2) {
          setCompanyName(data.companies.join(" vs "));
        } else if (!companyName) {
          setCompanyName(data.companies[0]);
        }
      } else if (!companyName) {
        // Fallback: extract from user's message
        const extracted = extractCompanyName(userMessage.content);
        if (extracted) setCompanyName(extracted);
      }

      if (data.ready_to_analyze) {
        setShowConfirmation(true);
      }
    } catch (error: any) {
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

  // Company name extraction helper (fallback when backend doesn't detect)
  const extractCompanyName = (text: string): string | null => {
    // 1. Comparison pattern: "Compare X vs Y"
    const vsMatch = text.match(
      /(?:compare|comparing|comparison of)?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:vs\.?|versus|and|\+)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)/i
    );
    if (vsMatch && vsMatch[1] && vsMatch[2]) {
      return `${vsMatch[1].trim()} vs ${vsMatch[2].trim()}`;
    }
    // 2. Single company patterns
    const patterns = [
      /(?:analyze|analysis of|about|research|look into|check out|review|compare)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)/i,
      /\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\b/,
    ];
    for (const p of patterns) {
      const match = text.match(p);
      if (match && match[1] && match[1].length > 2) return match[1];
    }
    return null;
  };

  // ==================== Start Analysis ====================

  // Detect if this is a comparison (companyName contains " vs " or " versus ")
  const isComparisonMode = / vs\.? |versus | and | \+ /i.test(companyName);
  const detectedCompanies = isComparisonMode
    ? companyName.split(/ vs\.?\s+| versus | and | \+ /i).map((c) => c.trim()).filter(Boolean)
    : [companyName];

  const handleStartAnalysis = async () => {
    setIsAnalyzing(true);
    setShowConfirmation(false);
    setComparisonResult(null);
    setComparisonId(null);

    const chatHistory = messages
      .filter((m) => m.role === "user" || m.role === "assistant")
      .map((m) => ({ role: m.role, content: m.content }));

    if (isComparisonMode && detectedCompanies.length >= 2) {
      // ── Comparison flow ──
      const statusMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: `🔍 Starting comparison of **${detectedCompanies.join(" vs ")}**. Running analysis for each company in parallel — this may take 30-90 seconds...`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, statusMessage]);

      try {
        const result = await runComparison({
          session_id: sessionId || "",
          companies: detectedCompanies,
          industry: industry || undefined,
          chat_history: chatHistory,
        });

        setComparisonResult(result.comparison);
        setComparisonId(result.comparison_id);

        const doneMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: `✅ Comparison complete! See the side-by-side analysis below.`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, doneMsg]);
      } catch (error: any) {
        const errorMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: `❌ Comparison failed: ${error.message}. Please try again.`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsAnalyzing(false);
      }
    } else {
      // ── Single-company flow (existing) ──
      const statusMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: `🔍 Starting comprehensive analysis for **${companyName || "the company"}**. This may take 30-60 seconds...`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, statusMessage]);

      try {
        const result = await runAnalysis({
          session_id: sessionId,
          company_name: companyName || "Company",
          industry: industry || "Technology",
          chat_history: chatHistory,
          output_format: ["pdf", "ppt"],
        });

        setAnalysisResult(result);

        const completeMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: `✅ Analysis complete for **${result.company_name}**!\n\n${result.summary || "Analysis has been generated successfully."}\n\n⏱️ Completed in ${result.execution_time?.toFixed(1) || "N/A"}s`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, completeMessage]);
      } catch (error: any) {
        const errorMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: `❌ Analysis failed: ${error.message}. Please try again.`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsAnalyzing(false);
      }
    }
  };

  // ==================== Download Comparison ====================

  const handleDownloadComparison = async (format: "pdf" | "ppt") => {
    if (!comparisonId) return;
    setIsDownloading(true);
    try {
      const result = await downloadComparison(comparisonId, format);
      // Trigger download
      const link = document.createElement("a");
      link.href = `${API_BASE_URL}${result.download_url}`;
      link.download = result.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error: any) {
      const errMsg: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: `❌ Download failed: ${error.message}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsDownloading(false);
    }
  };

  // ==================== Render ====================

  if (isLoading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", background: "#0a0a0f" }}>
        <div className="page-spinner" />
        <style jsx>{`.page-spinner { width: 32px; height: 32px; border: 3px solid rgba(124, 58, 237, 0.2); border-top-color: #7c3aed; border-radius: 50%; animation: spin 0.7s linear infinite; } @keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div className="chat-page">
      {/* Messages Area */}
      <div className="messages-area">
        {showPrompts && messages.length === 0 ? (
          <div className="welcome">
            <div className="welcome-icon">
              <Sparkles size={32} />
            </div>
            <h1 className="welcome-title">
              Welcome{user ? `, ${user.name.split(" ")[0]}` : ""}
            </h1>
            <p className="welcome-subtitle">
              What strategic question can I help you with today?
            </p>
            <div className="suggestions-grid">
              {promptSuggestions.map((s, i) => (
                <button
                  key={i}
                  className="suggestion-card"
                  onClick={() => {
                    setInput(s.description);
                    inputRef.current?.focus();
                  }}
                >
                  <span className="suggestion-emoji">{s.icon}</span>
                  <span className="suggestion-title">{s.title}</span>
                  <span className="suggestion-desc">{s.description}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === "user" ? (
                    <span className="avatar-user">
                      {user?.name?.[0]?.toUpperCase() || "U"}
                    </span>
                  ) : (
                    <span className="avatar-ai">
                      <Sparkles size={16} />
                    </span>
                  )}
                </div>
                <div className="message-content">
                  <div className="message-role">
                    {msg.role === "user" ? user?.name || "You" : "Origin Labs"}
                  </div>
                  <div className="message-text">{msg.content}</div>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="message assistant">
                <div className="message-avatar">
                  <span className="avatar-ai">
                    <Sparkles size={16} />
                  </span>
                </div>
                <div className="message-content">
                  <div className="message-role">Origin Labs</div>
                  <div className="typing-dots">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}

            {showConfirmation && !isAnalyzing && (
              <div className="confirmation-bar">
                <p>
                  {isComparisonMode
                    ? `Ready to compare ${detectedCompanies.join(" vs ")}?`
                    : "Ready to start the comprehensive analysis?"}
                </p>
                <div className="confirmation-actions">
                  <button className="confirm-btn" onClick={handleStartAnalysis}>
                    {isComparisonMode ? "Start Comparison" : "Start Analysis"}
                  </button>
                  <button className="cancel-btn" onClick={() => setShowConfirmation(false)}>
                    Not yet
                  </button>
                </div>
              </div>
            )}

            {isAnalyzing && (
              <div className="analyzing-bar">
                <RefreshCw size={18} className="spin" />
                <span>{isComparisonMode ? "Comparing companies — running parallel analysis..." : "Running multi-agent analysis..."}</span>
              </div>
            )}

            {/* ── Comparison Table ── */}
            {comparisonResult && comparisonResult.categories?.length > 0 && (
              <div className="comparison-section">
                <h2 className="comparison-title">{comparisonResult.title}</h2>

                {comparisonResult.categories.map((cat, ci) => (
                  <div key={ci} className="comparison-category">
                    <h3 className="category-name">{cat.name}</h3>
                    <div className="comparison-table-wrap">
                      <table className="comparison-table">
                        <thead>
                          <tr>
                            <th>Metric</th>
                            {comparisonResult.companies.map((c, i) => (
                              <th key={i}>{c}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {cat.rows.map((row, ri) => (
                            <tr key={ri}>
                              <td className="metric-cell">{row.metric}</td>
                              {comparisonResult.companies.map((_, i) => (
                                <td key={i}>{row[`company_${i}`] || "N/A"}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}

                {comparisonResult.verdict && (
                  <div className="verdict-box">
                    <strong>Verdict:</strong> {comparisonResult.verdict}
                  </div>
                )}

                {/* Download choice */}
                <div className="download-choice">
                  <p>Would you like to download this comparison?</p>
                  <div className="download-btns">
                    <button
                      className="dl-btn dl-pdf"
                      onClick={() => handleDownloadComparison("pdf")}
                      disabled={isDownloading}
                    >
                      <Download size={16} /> Download PDF
                    </button>
                    <button
                      className="dl-btn dl-ppt"
                      onClick={() => handleDownloadComparison("ppt")}
                      disabled={isDownloading}
                    >
                      <Download size={16} /> Download PPT
                    </button>
                  </div>
                </div>
              </div>
            )}

            {analysisResult?.output_urls?.length > 0 && (
              <div className="downloads">
                <p className="downloads-title">📎 Downloads</p>
                {analysisResult.output_urls.map((url: string, i: number) => (
                  <a
                    key={i}
                    href={`${API_BASE_URL}/download/${url}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="download-link"
                  >
                    {url.endsWith(".pdf") ? "📄 PDF Report" : "📊 Pitch Deck"}
                  </a>
                ))}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="input-area">
        {/* Uploaded docs chips */}
        {uploadedDocs.length > 0 && (
          <div className="doc-chips">
            {uploadedDocs.slice(0, 5).map((doc) => (
              <span key={doc.id} className="doc-chip">
                <FileText size={12} />
                <span className="doc-chip-name">{doc.filename}</span>
                <button className="doc-chip-remove" onClick={() => handleDeleteDoc(doc.id)}>
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Upload error */}
        {uploadError && (
          <div className="upload-error">{uploadError}</div>
        )}

        <div className="input-container">
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            style={{ display: "none" }}
          />

          {/* Upload button */}
          <button
            className="attach-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading || isAnalyzing}
            title="Upload PDF"
          >
            {isUploading ? <Loader2 size={18} className="spin" /> : <Paperclip size={18} />}
          </button>

          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={isUploading ? "Uploading document..." : isAnalyzing ? "Analysis in progress..." : "Ask about any company..."}
            disabled={isAnalyzing || isUploading}
            rows={1}
            className="chat-input"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isTyping || isAnalyzing || isUploading}
            className="send-btn"
          >
            <Send size={18} />
          </button>
        </div>
        <p className="input-hint">
          Origin Labs can make mistakes. Verify important analysis.
        </p>
      </div>

      <style jsx>{`
        .chat-page {
          display: flex;
          flex-direction: column;
          height: 100vh;
          background: #0a0a0f;
        }

        /* Messages Area */
        .messages-area {
          flex: 1;
          overflow-y: auto;
          padding: 0 16px;
        }

        .messages-area::-webkit-scrollbar {
          width: 6px;
        }
        .messages-area::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
        }

        /* Welcome */
        .welcome {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: calc(100vh - 160px);
          text-align: center;
          padding: 40px 20px;
        }

        .welcome-icon {
          width: 64px;
          height: 64px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #7c3aed, #6366f1);
          border-radius: 16px;
          color: #fff;
          margin-bottom: 20px;
        }

        .welcome-title {
          color: #fff;
          font-size: 28px;
          font-weight: 700;
          margin: 0 0 8px;
        }

        .welcome-subtitle {
          color: rgba(255, 255, 255, 0.45);
          font-size: 15px;
          margin: 0 0 36px;
        }

        .suggestions-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
          max-width: 520px;
          width: 100%;
        }

        .suggestion-card {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: 4px;
          padding: 16px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          cursor: pointer;
          text-align: left;
          transition: background 0.15s, border-color 0.15s;
          color: #fff;
        }

        .suggestion-card:hover {
          background: rgba(255, 255, 255, 0.06);
          border-color: rgba(124, 58, 237, 0.3);
        }

        .suggestion-emoji {
          font-size: 20px;
          margin-bottom: 4px;
        }

        .suggestion-title {
          font-size: 13px;
          font-weight: 600;
          color: #fff;
        }

        .suggestion-desc {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.4);
        }

        /* Messages */
        .messages-list {
          max-width: 780px;
          margin: 0 auto;
          padding: 20px 0 100px;
        }

        .message {
          display: flex;
          gap: 14px;
          padding: 20px 0;
        }

        .message + .message {
          border-top: 1px solid rgba(255, 255, 255, 0.04);
        }

        .message-avatar {
          flex-shrink: 0;
        }

        .avatar-user {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #3b82f6, #06b6d4);
          border-radius: 8px;
          color: #fff;
          font-size: 14px;
          font-weight: 700;
        }

        .avatar-ai {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #7c3aed, #a78bfa);
          border-radius: 8px;
          color: #fff;
        }

        .message-content {
          flex: 1;
          min-width: 0;
        }

        .message-role {
          font-size: 13px;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.8);
          margin-bottom: 4px;
        }

        .message-text {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.7);
          line-height: 1.6;
          white-space: pre-wrap;
          word-break: break-word;
        }

        /* Typing indicator */
        .typing-dots {
          display: flex;
          gap: 4px;
          padding: 4px 0;
        }

        .typing-dots span {
          width: 8px;
          height: 8px;
          background: rgba(255, 255, 255, 0.3);
          border-radius: 50%;
          animation: bounce 1.4s infinite ease-in-out;
        }

        .typing-dots span:nth-child(1) { animation-delay: 0s; }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0.8); opacity: 0.3; }
          40% { transform: scale(1.2); opacity: 1; }
        }

        /* Confirmation */
        .confirmation-bar {
          max-width: 780px;
          margin: 16px auto;
          padding: 16px 20px;
          background: rgba(124, 58, 237, 0.08);
          border: 1px solid rgba(124, 58, 237, 0.2);
          border-radius: 12px;
          text-align: center;
        }

        .confirmation-bar p {
          color: rgba(255, 255, 255, 0.8);
          font-size: 14px;
          margin: 0 0 12px;
        }

        .confirmation-actions {
          display: flex;
          gap: 10px;
          justify-content: center;
        }

        .confirm-btn {
          padding: 8px 20px;
          background: linear-gradient(135deg, #7c3aed, #6366f1);
          border: none;
          border-radius: 8px;
          color: #fff;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.15s;
        }

        .confirm-btn:hover { opacity: 0.9; }

        .cancel-btn {
          padding: 8px 20px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: rgba(255, 255, 255, 0.6);
          font-size: 13px;
          cursor: pointer;
          transition: background 0.15s;
        }

        .cancel-btn:hover { background: rgba(255, 255, 255, 0.1); }

        /* Analyzing */
        .analyzing-bar {
          display: flex;
          align-items: center;
          gap: 10px;
          justify-content: center;
          padding: 16px;
          color: #a78bfa;
          font-size: 14px;
        }

        .analyzing-bar :global(.spin) {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        /* Downloads */
        .downloads {
          max-width: 780px;
          margin: 12px auto;
          padding: 16px 20px;
          background: rgba(34, 197, 94, 0.06);
          border: 1px solid rgba(34, 197, 94, 0.15);
          border-radius: 12px;
        }

        .downloads-title {
          font-size: 13px;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.7);
          margin: 0 0 10px;
        }

        .download-link {
          display: inline-block;
          padding: 6px 14px;
          margin-right: 8px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: #a78bfa;
          font-size: 13px;
          text-decoration: none;
          transition: background 0.15s;
        }

        .download-link:hover {
          background: rgba(255, 255, 255, 0.1);
        }

        /* Input Area */
        .input-area {
          padding: 16px;
          border-top: 1px solid rgba(255, 255, 255, 0.04);
        }

        .doc-chips {
          max-width: 780px;
          margin: 0 auto 8px;
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }

        .doc-chip {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          background: rgba(124, 58, 237, 0.12);
          border: 1px solid rgba(124, 58, 237, 0.25);
          border-radius: 8px;
          font-size: 12px;
          color: #a78bfa;
        }

        .doc-chip-name {
          max-width: 120px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .doc-chip-remove {
          background: none;
          border: none;
          color: rgba(255, 255, 255, 0.35);
          cursor: pointer;
          padding: 0;
          display: flex;
        }

        .doc-chip-remove:hover {
          color: #ef4444;
        }

        .upload-error {
          max-width: 780px;
          margin: 0 auto 8px;
          padding: 8px 14px;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.25);
          border-radius: 8px;
          color: #ef4444;
          font-size: 12px;
        }

        .input-container {
          max-width: 780px;
          margin: 0 auto;
          display: flex;
          align-items: flex-end;
          gap: 8px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 14px;
          padding: 8px 12px;
          transition: border-color 0.2s;
        }

        .input-container:focus-within {
          border-color: rgba(124, 58, 237, 0.4);
        }

        .attach-btn {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: none;
          border: none;
          color: rgba(255, 255, 255, 0.4);
          cursor: pointer;
          border-radius: 8px;
          flex-shrink: 0;
          transition: background 0.15s, color 0.15s;
        }

        .attach-btn:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.08);
          color: #a78bfa;
        }

        .attach-btn:disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }

        .attach-btn :global(.spin) {
          animation: spin 1s linear infinite;
        }

        .chat-input {
          flex: 1;
          background: none;
          border: none;
          color: #fff;
          font-size: 14px;
          line-height: 1.5;
          resize: none;
          outline: none;
          max-height: 200px;
          padding: 6px 0;
        }

        .chat-input::placeholder {
          color: rgba(255, 255, 255, 0.25);
        }

        .send-btn {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #7c3aed, #6366f1);
          border: none;
          border-radius: 10px;
          color: #fff;
          cursor: pointer;
          flex-shrink: 0;
          transition: opacity 0.15s, transform 0.15s;
        }

        .send-btn:hover:not(:disabled) {
          transform: scale(1.05);
        }

        .send-btn:disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }

        .input-hint {
          max-width: 780px;
          margin: 8px auto 0;
          text-align: center;
          color: rgba(255, 255, 255, 0.2);
          font-size: 11px;
        }

        /* Comparison Section */
        .comparison-section {
          max-width: 780px;
          margin: 20px auto;
          padding: 24px;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(124, 58, 237, 0.15);
          border-radius: 16px;
        }

        .comparison-title {
          font-size: 20px;
          font-weight: 700;
          color: #fff;
          text-align: center;
          margin: 0 0 20px;
        }

        .comparison-category {
          margin-bottom: 20px;
        }

        .category-name {
          font-size: 15px;
          font-weight: 600;
          color: #a78bfa;
          margin: 0 0 10px;
          padding-bottom: 6px;
          border-bottom: 1px solid rgba(124, 58, 237, 0.15);
        }

        .comparison-table-wrap {
          overflow-x: auto;
          border-radius: 10px;
          border: 1px solid rgba(255, 255, 255, 0.06);
        }

        .comparison-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 13px;
        }

        .comparison-table thead th {
          background: rgba(124, 58, 237, 0.25);
          color: #e0d4ff;
          font-weight: 600;
          padding: 10px 14px;
          text-align: left;
          white-space: nowrap;
        }

        .comparison-table tbody td {
          padding: 10px 14px;
          color: rgba(255, 255, 255, 0.75);
          border-top: 1px solid rgba(255, 255, 255, 0.04);
          vertical-align: top;
        }

        .comparison-table tbody tr:nth-child(even) td {
          background: rgba(255, 255, 255, 0.02);
        }

        .comparison-table tbody tr:hover td {
          background: rgba(124, 58, 237, 0.06);
        }

        .metric-cell {
          font-weight: 600;
          color: rgba(255, 255, 255, 0.9) !important;
          white-space: nowrap;
        }

        .verdict-box {
          margin-top: 16px;
          padding: 14px 18px;
          background: linear-gradient(135deg, rgba(124, 58, 237, 0.08), rgba(99, 102, 241, 0.08));
          border: 1px solid rgba(124, 58, 237, 0.2);
          border-radius: 10px;
          color: rgba(255, 255, 255, 0.85);
          font-size: 14px;
          line-height: 1.5;
        }

        .download-choice {
          margin-top: 20px;
          text-align: center;
        }

        .download-choice p {
          color: rgba(255, 255, 255, 0.6);
          font-size: 14px;
          margin: 0 0 12px;
        }

        .download-btns {
          display: flex;
          gap: 12px;
          justify-content: center;
        }

        .dl-btn {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 10px 22px;
          border: none;
          border-radius: 10px;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.15s, transform 0.15s;
          color: #fff;
        }

        .dl-btn:hover:not(:disabled) {
          transform: scale(1.03);
        }

        .dl-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        .dl-pdf {
          background: linear-gradient(135deg, #3b82f6, #6366f1);
        }

        .dl-ppt {
          background: linear-gradient(135deg, #f59e0b, #ef4444);
        }
      `}</style>
    </div>
  );
}
