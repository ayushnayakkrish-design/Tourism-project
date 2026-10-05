import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { usersApi, authApi } from "@/api/auth";
import type { PublicUser, AuthResponse, Role, UserPreferences } from "@/api/types";

interface AuthContextValue {
  user: PublicUser | null;
  preferences: UserPreferences | null;
  role: Role | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; display_name: string }) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  updatePreferences: (prefs: Partial<UserPreferences>) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<PublicUser | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const role = user?.role ?? null;

  const loadSession = useCallback(async () => {
    const token = localStorage.getItem("wandor_token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const [u, prefs] = await Promise.all([
        authApi.me(),
        usersApi.getPreferences().catch(() => null),
      ]);
      setUser(u);
      setPreferences(prefs);
    } catch {
      localStorage.removeItem("wandor_token");
      localStorage.removeItem("wandor_user");
      setUser(null);
      setPreferences(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  const login = async (email: string, password: string) => {
    const res = await authApi.login({ email, password });
    localStorage.setItem("wandor_token", res.access_token);
    localStorage.setItem("wandor_user", JSON.stringify(res.user));
    setUser(res.user);
    const prefs = await usersApi.getPreferences().catch(() => null);
    setPreferences(prefs);
  };

  const register = async (data: { email: string; password: string; display_name: string }) => {
    const res = await authApi.register(data);
    localStorage.setItem("wandor_token", res.access_token);
    localStorage.setItem("wandor_user", JSON.stringify(res.user));
    setUser(res.user);
    const prefs = await usersApi.getPreferences().catch(() => null);
    setPreferences(prefs);
  };

  const logout = () => {
    localStorage.removeItem("wandor_token");
    localStorage.removeItem("wandor_user");
    setUser(null);
    setPreferences(null);
  };

  const refreshUser = async () => {
    await loadSession();
  };

  const updatePreferences = async (prefs: Partial<UserPreferences>) => {
    const updated = await usersApi.updatePreferences(prefs);
    setPreferences(updated);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        preferences,
        role,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
        updatePreferences,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}