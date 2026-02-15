"use client";

import React, { useState, useCallback } from "react";
import Sidebar from "@/components/Sidebar";

export default function ChatLayout({ children }: { children: React.ReactNode }) {
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    const handleSelectSession = useCallback((sessionId: string) => {
        setActiveSessionId(sessionId);
        // Dispatch custom event so the chat page can react
        window.dispatchEvent(
            new CustomEvent("sidebar:selectSession", { detail: { sessionId } })
        );
    }, []);

    const handleNewChat = useCallback(() => {
        setActiveSessionId(null);
        window.dispatchEvent(new CustomEvent("sidebar:newChat"));
    }, []);

    // Listen for session updates from chat page
    React.useEffect(() => {
        const handleSessionUpdate = (e: Event) => {
            const detail = (e as CustomEvent).detail;
            if (detail?.sessionId) {
                setActiveSessionId(detail.sessionId);
            }
            setRefreshTrigger((p) => p + 1);
        };

        window.addEventListener("chat:sessionUpdated", handleSessionUpdate);
        return () => window.removeEventListener("chat:sessionUpdated", handleSessionUpdate);
    }, []);

    return (
        <div style={{ display: "flex", height: "100vh", background: "#0a0a0f" }}>
            <Sidebar
                activeSessionId={activeSessionId}
                onSelectSession={handleSelectSession}
                onNewChat={handleNewChat}
                refreshTrigger={refreshTrigger}
            />
            <div style={{ flex: 1, overflow: "hidden" }}>{children}</div>
        </div>
    );
}
