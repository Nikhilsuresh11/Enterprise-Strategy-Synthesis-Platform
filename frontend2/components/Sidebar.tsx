"use client";

import React, { useState, useEffect, useRef } from "react";
import {
    Plus,
    MessageSquare,
    Trash2,
    Pencil,
    Check,
    X,
    LogOut,
    PanelLeftClose,
    PanelLeft,
    User,
} from "lucide-react";
import { ChatSession, getChatSessions, deleteChatSession, updateSessionTitle } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";

interface SidebarProps {
    activeSessionId: string | null;
    onSelectSession: (sessionId: string) => void;
    onNewChat: () => void;
    refreshTrigger?: number;
}

// Group sessions by date category
function groupByDate(sessions: ChatSession[]) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 86400000);
    const lastWeek = new Date(today.getTime() - 7 * 86400000);

    const groups: { label: string; sessions: ChatSession[] }[] = [
        { label: "Today", sessions: [] },
        { label: "Yesterday", sessions: [] },
        { label: "Previous 7 Days", sessions: [] },
        { label: "Older", sessions: [] },
    ];

    for (const s of sessions) {
        const d = new Date(s.updated_at);
        if (d >= today) groups[0].sessions.push(s);
        else if (d >= yesterday) groups[1].sessions.push(s);
        else if (d >= lastWeek) groups[2].sessions.push(s);
        else groups[3].sessions.push(s);
    }

    return groups.filter((g) => g.sessions.length > 0);
}

export default function Sidebar({
    activeSessionId,
    onSelectSession,
    onNewChat,
    refreshTrigger = 0,
}: SidebarProps) {
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [collapsed, setCollapsed] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editTitle, setEditTitle] = useState("");
    const [loading, setLoading] = useState(true);
    const editInputRef = useRef<HTMLInputElement>(null);
    const { user, logout } = useAuth();

    // Fetch sessions
    useEffect(() => {
        let mounted = true;
        const fetchSessions = async () => {
            try {
                const data = await getChatSessions();
                if (mounted) {
                    setSessions(data);
                    setLoading(false);
                }
            } catch {
                if (mounted) setLoading(false);
            }
        };
        fetchSessions();
        return () => { mounted = false; };
    }, [refreshTrigger]);

    // Focus edit input
    useEffect(() => {
        if (editingId && editInputRef.current) {
            editInputRef.current.focus();
            editInputRef.current.select();
        }
    }, [editingId]);

    const handleDelete = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await deleteChatSession(id);
            setSessions((prev) => prev.filter((s) => s.id !== id));
            if (activeSessionId === id) onNewChat();
        } catch { }
    };

    const handleRename = (id: string, currentTitle: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setEditingId(id);
        setEditTitle(currentTitle);
    };

    const handleRenameSubmit = async (id: string) => {
        if (editTitle.trim()) {
            try {
                await updateSessionTitle(id, editTitle.trim());
                setSessions((prev) =>
                    prev.map((s) => (s.id === id ? { ...s, title: editTitle.trim() } : s))
                );
            } catch { }
        }
        setEditingId(null);
    };

    const groups = groupByDate(sessions);

    if (collapsed) {
        return (
            <div className="sidebar-collapsed">
                <button className="sidebar-toggle" onClick={() => setCollapsed(false)} title="Open sidebar">
                    <PanelLeft size={20} />
                </button>
                <button className="sidebar-new-mini" onClick={onNewChat} title="New chat">
                    <Plus size={20} />
                </button>
                <style jsx>{`
          .sidebar-collapsed {
            width: 50px;
            height: 100vh;
            background: #111118;
            border-right: 1px solid rgba(255, 255, 255, 0.06);
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 12px;
            gap: 8px;
            flex-shrink: 0;
          }
          .sidebar-toggle,
          .sidebar-new-mini {
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: none;
            border: none;
            color: rgba(255, 255, 255, 0.5);
            cursor: pointer;
            border-radius: 8px;
            transition: background 0.15s, color 0.15s;
          }
          .sidebar-toggle:hover,
          .sidebar-new-mini:hover {
            background: rgba(255, 255, 255, 0.08);
            color: #fff;
          }
        `}</style>
            </div>
        );
    }

    return (
        <div className="sidebar">
            {/* Header */}
            <div className="sidebar-header">
                <button className="new-chat-btn" onClick={onNewChat}>
                    <Plus size={18} />
                    <span>New Chat</span>
                </button>
                <button
                    className="sidebar-toggle"
                    onClick={() => setCollapsed(true)}
                    title="Close sidebar"
                >
                    <PanelLeftClose size={20} />
                </button>
            </div>

            {/* Session List */}
            <div className="sidebar-sessions">
                {loading ? (
                    <div className="sidebar-loading">
                        <div className="dot-pulse" />
                    </div>
                ) : sessions.length === 0 ? (
                    <div className="sidebar-empty">
                        <MessageSquare size={24} />
                        <p>No conversations yet</p>
                    </div>
                ) : (
                    groups.map((group) => (
                        <div key={group.label} className="session-group">
                            <div className="group-label">{group.label}</div>
                            {group.sessions.map((session) => (
                                <div
                                    key={session.id}
                                    className={`session-item ${session.id === activeSessionId ? "active" : ""
                                        }`}
                                    onClick={() => onSelectSession(session.id)}
                                >
                                    {editingId === session.id ? (
                                        <div className="session-edit">
                                            <input
                                                ref={editInputRef}
                                                value={editTitle}
                                                onChange={(e) => setEditTitle(e.target.value)}
                                                onKeyDown={(e) => {
                                                    if (e.key === "Enter") handleRenameSubmit(session.id);
                                                    if (e.key === "Escape") setEditingId(null);
                                                }}
                                                onClick={(e) => e.stopPropagation()}
                                                className="edit-input"
                                            />
                                            <button
                                                className="edit-action"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleRenameSubmit(session.id);
                                                }}
                                            >
                                                <Check size={14} />
                                            </button>
                                            <button
                                                className="edit-action"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setEditingId(null);
                                                }}
                                            >
                                                <X size={14} />
                                            </button>
                                        </div>
                                    ) : (
                                        <>
                                            <MessageSquare size={15} className="session-icon" />
                                            <span className="session-title">{session.title}</span>
                                            <div className="session-actions">
                                                <button
                                                    className="session-action"
                                                    onClick={(e) => handleRename(session.id, session.title, e)}
                                                    title="Rename"
                                                >
                                                    <Pencil size={13} />
                                                </button>
                                                <button
                                                    className="session-action session-action-danger"
                                                    onClick={(e) => handleDelete(session.id, e)}
                                                    title="Delete"
                                                >
                                                    <Trash2 size={13} />
                                                </button>
                                            </div>
                                        </>
                                    )}
                                </div>
                            ))}
                        </div>
                    ))
                )}
            </div>

            {/* User Info */}
            <div className="sidebar-footer">
                <div className="user-info">
                    <div className="user-avatar">
                        <User size={16} />
                    </div>
                    <span className="user-name">{user?.name || "User"}</span>
                </div>
                <button className="logout-btn" onClick={logout} title="Sign out">
                    <LogOut size={16} />
                </button>
            </div>

            <style jsx>{`
        .sidebar {
          width: 260px;
          height: 100vh;
          background: #111118;
          border-right: 1px solid rgba(255, 255, 255, 0.06);
          display: flex;
          flex-direction: column;
          flex-shrink: 0;
        }

        .sidebar-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .new-chat-btn {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 14px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 10px;
          color: #fff;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.15s;
        }

        .new-chat-btn:hover {
          background: rgba(255, 255, 255, 0.1);
        }

        .sidebar-toggle {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: none;
          border: none;
          color: rgba(255, 255, 255, 0.5);
          cursor: pointer;
          border-radius: 8px;
          transition: background 0.15s, color 0.15s;
          flex-shrink: 0;
        }

        .sidebar-toggle:hover {
          background: rgba(255, 255, 255, 0.08);
          color: #fff;
        }

        .sidebar-sessions {
          flex: 1;
          overflow-y: auto;
          padding: 8px;
        }

        .sidebar-sessions::-webkit-scrollbar {
          width: 4px;
        }
        .sidebar-sessions::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
        }

        .sidebar-loading {
          display: flex;
          justify-content: center;
          padding: 24px;
        }

        .dot-pulse {
          width: 8px;
          height: 8px;
          background: rgba(255, 255, 255, 0.3);
          border-radius: 50%;
          animation: pulse 1s ease-in-out infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 1; }
        }

        .sidebar-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 32px 16px;
          color: rgba(255, 255, 255, 0.25);
          font-size: 13px;
        }

        .session-group {
          margin-bottom: 8px;
        }

        .group-label {
          padding: 6px 12px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: rgba(255, 255, 255, 0.3);
        }

        .session-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          border-radius: 8px;
          cursor: pointer;
          transition: background 0.15s;
          position: relative;
          min-height: 36px;
        }

        .session-item:hover {
          background: rgba(255, 255, 255, 0.06);
        }

        .session-item.active {
          background: rgba(124, 58, 237, 0.15);
        }

        .session-item :global(.session-icon) {
          flex-shrink: 0;
          color: rgba(255, 255, 255, 0.35);
        }

        .session-title {
          flex: 1;
          font-size: 13px;
          color: rgba(255, 255, 255, 0.8);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .session-actions {
          display: none;
          gap: 2px;
        }

        .session-item:hover .session-actions {
          display: flex;
        }

        .session-action {
          width: 26px;
          height: 26px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: none;
          border: none;
          color: rgba(255, 255, 255, 0.4);
          cursor: pointer;
          border-radius: 6px;
          transition: background 0.15s, color 0.15s;
        }

        .session-action:hover {
          background: rgba(255, 255, 255, 0.1);
          color: #fff;
        }

        .session-action-danger:hover {
          color: #ef4444;
        }

        .session-edit {
          display: flex;
          align-items: center;
          gap: 4px;
          flex: 1;
        }

        .edit-input {
          flex: 1;
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(124, 58, 237, 0.4);
          border-radius: 6px;
          padding: 4px 8px;
          color: #fff;
          font-size: 13px;
          outline: none;
        }

        .edit-action {
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: none;
          border: none;
          color: rgba(255, 255, 255, 0.5);
          cursor: pointer;
          border-radius: 4px;
        }

        .edit-action:hover {
          color: #fff;
        }

        .sidebar-footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px;
          border-top: 1px solid rgba(255, 255, 255, 0.06);
        }

        .user-info {
          display: flex;
          align-items: center;
          gap: 10px;
          flex: 1;
          min-width: 0;
        }

        .user-avatar {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #7c3aed, #6366f1);
          border-radius: 8px;
          color: #fff;
          flex-shrink: 0;
        }

        .user-name {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.8);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .logout-btn {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: none;
          border: none;
          color: rgba(255, 255, 255, 0.4);
          cursor: pointer;
          border-radius: 8px;
          transition: background 0.15s, color 0.15s;
          flex-shrink: 0;
        }

        .logout-btn:hover {
          background: rgba(239, 68, 68, 0.15);
          color: #ef4444;
        }
      `}</style>
        </div>
    );
}
