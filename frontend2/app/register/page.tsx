"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { registerUser } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import { ArrowRight, Eye, EyeOff, Sparkles } from "lucide-react";

export default function RegisterPage() {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        if (password.length < 6) {
            setError("Password must be at least 6 characters");
            return;
        }

        setLoading(true);

        try {
            const data = await registerUser({ name, email, password });
            login(data.access_token, data.user);
            router.push("/chat");
        } catch (err: any) {
            setError(err.message || "Registration failed. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="register-page">
            <div className="register-bg">
                <div className="register-glow register-glow-1" />
                <div className="register-glow register-glow-2" />
            </div>

            <div className="register-container">
                <div className="register-logo">
                    <Sparkles size={28} />
                    <span>Origin Labs</span>
                </div>

                <h1 className="register-title">Create account</h1>
                <p className="register-subtitle">
                    Start building strategic intelligence
                </p>

                {error && <div className="register-error">{error}</div>}

                <form onSubmit={handleSubmit} className="register-form">
                    <div className="form-group">
                        <label htmlFor="name">Full Name</label>
                        <input
                            id="name"
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="John Doe"
                            required
                            autoComplete="name"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@company.com"
                            required
                            autoComplete="email"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <div className="password-wrapper">
                            <input
                                id="password"
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Min 6 characters"
                                required
                                autoComplete="new-password"
                            />
                            <button
                                type="button"
                                className="password-toggle"
                                onClick={() => setShowPassword(!showPassword)}
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="confirm-password">Confirm Password</label>
                        <input
                            id="confirm-password"
                            type={showPassword ? "text" : "password"}
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            placeholder="Repeat password"
                            required
                            autoComplete="new-password"
                        />
                    </div>

                    <button type="submit" className="register-btn" disabled={loading}>
                        {loading ? (
                            <div className="btn-spinner" />
                        ) : (
                            <>
                                Create Account
                                <ArrowRight size={18} />
                            </>
                        )}
                    </button>
                </form>

                <p className="register-footer">
                    Already have an account?{" "}
                    <Link href="/login">Sign in</Link>
                </p>
            </div>

            <style jsx>{`
        .register-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #0a0a0f;
          position: relative;
          overflow: hidden;
        }

        .register-bg {
          position: absolute;
          inset: 0;
          z-index: 0;
        }

        .register-glow {
          position: absolute;
          border-radius: 50%;
          filter: blur(120px);
          opacity: 0.3;
        }

        .register-glow-1 {
          width: 400px;
          height: 400px;
          top: -100px;
          left: -100px;
          background: linear-gradient(135deg, #7c3aed, #a78bfa);
        }

        .register-glow-2 {
          width: 350px;
          height: 350px;
          bottom: -80px;
          right: -80px;
          background: linear-gradient(135deg, #6366f1, #3b82f6);
        }

        .register-container {
          position: relative;
          z-index: 1;
          width: 100%;
          max-width: 420px;
          padding: 40px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 20px;
          backdrop-filter: blur(20px);
          margin: 20px;
        }

        .register-logo {
          display: flex;
          align-items: center;
          gap: 10px;
          color: #a78bfa;
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 32px;
        }

        .register-title {
          color: #fff;
          font-size: 28px;
          font-weight: 700;
          margin: 0 0 8px;
        }

        .register-subtitle {
          color: rgba(255, 255, 255, 0.5);
          font-size: 14px;
          margin: 0 0 28px;
        }

        .register-error {
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          color: #ef4444;
          padding: 12px 16px;
          border-radius: 10px;
          font-size: 13px;
          margin-bottom: 20px;
        }

        .register-form {
          display: flex;
          flex-direction: column;
          gap: 18px;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .form-group label {
          color: rgba(255, 255, 255, 0.7);
          font-size: 13px;
          font-weight: 500;
        }

        .form-group input {
          width: 100%;
          padding: 12px 16px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 10px;
          color: #fff;
          font-size: 14px;
          transition: border-color 0.2s, box-shadow 0.2s;
          outline: none;
          box-sizing: border-box;
        }

        .form-group input:focus {
          border-color: #7c3aed;
          box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15);
        }

        .form-group input::placeholder {
          color: rgba(255, 255, 255, 0.25);
        }

        .password-wrapper {
          position: relative;
        }

        .password-toggle {
          position: absolute;
          right: 12px;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          color: rgba(255, 255, 255, 0.4);
          cursor: pointer;
          padding: 4px;
          display: flex;
        }

        .password-toggle:hover {
          color: rgba(255, 255, 255, 0.7);
        }

        .register-btn {
          width: 100%;
          padding: 14px;
          background: linear-gradient(135deg, #7c3aed, #6366f1);
          border: none;
          border-radius: 10px;
          color: #fff;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          transition: transform 0.15s, opacity 0.15s;
          margin-top: 4px;
        }

        .register-btn:hover:not(:disabled) {
          transform: translateY(-1px);
          opacity: 0.95;
        }

        .register-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: #fff;
          border-radius: 50%;
          animation: spin 0.6s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .register-footer {
          text-align: center;
          margin-top: 24px;
          color: rgba(255, 255, 255, 0.4);
          font-size: 14px;
        }

        .register-footer a,
        .register-footer :global(a) {
          color: #a78bfa;
          text-decoration: none;
          font-weight: 500;
        }

        .register-footer a:hover,
        .register-footer :global(a):hover {
          text-decoration: underline;
        }
      `}</style>
        </div>
    );
}
