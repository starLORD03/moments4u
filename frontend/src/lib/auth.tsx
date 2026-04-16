/**
 * Auth context and hooks for managing user state across the app.
 */

"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import { api, setAccessToken, getAccessToken } from "./api";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "teacher" | "parent";
  playgroup_id: string | null;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    role: string;
    playgroup_id?: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    const token = getAccessToken();
    if (token) {
      api.auth
        .me()
        .then(setUser)
        .catch(() => {
          setAccessToken(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const data = await api.auth.login(email, password);
    setAccessToken(data.access_token);
    setUser(data.user);
  }, []);

  const register = useCallback(
    async (regData: {
      email: string;
      password: string;
      full_name: string;
      role: string;
      playgroup_id?: string;
    }) => {
      const data = await api.auth.register(regData);
      setAccessToken(data.access_token);
      setUser(data.user);
    },
    []
  );

  const logout = useCallback(async () => {
    try {
      await api.auth.logout();
    } catch {
      // ignore
    }
    setAccessToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
