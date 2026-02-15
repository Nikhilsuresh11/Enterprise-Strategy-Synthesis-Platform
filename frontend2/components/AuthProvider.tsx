"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getToken, setToken, removeToken, getStoredUser, setStoredUser } from "@/lib/auth";
import { getCurrentUser } from "@/lib/api";

interface User {
    id: string;
    name: string;
    email: string;
    created_at: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    login: (token: string, user: User) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    token: null,
    isLoading: true,
    login: () => { },
    logout: () => { },
});

export function useAuth() {
    return useContext(AuthContext);
}

// Public routes that don't require authentication
const PUBLIC_ROUTES = ["/", "/login", "/register"];

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setTokenState] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    // Check for existing token on mount
    useEffect(() => {
        const initAuth = async () => {
            const storedToken = getToken();
            if (storedToken) {
                try {
                    const userData = await getCurrentUser();
                    setUser(userData);
                    setTokenState(storedToken);
                    setStoredUser(userData);
                } catch {
                    // Token is invalid or expired
                    removeToken();
                }
            }
            setIsLoading(false);
        };

        initAuth();
    }, []);

    // Redirect to login if unauthenticated on protected routes
    useEffect(() => {
        if (!isLoading && !user && !PUBLIC_ROUTES.includes(pathname)) {
            router.push("/login");
        }
    }, [isLoading, user, pathname, router]);

    const login = useCallback((newToken: string, userData: User) => {
        setToken(newToken);
        setStoredUser(userData);
        setUser(userData);
        setTokenState(newToken);
    }, []);

    const logout = useCallback(() => {
        removeToken();
        setUser(null);
        setTokenState(null);
        router.push("/login");
    }, [router]);

    return (
        <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}
