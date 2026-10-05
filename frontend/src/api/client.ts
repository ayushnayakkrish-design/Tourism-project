import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig } from "axios";
import type { ApiErrorBody } from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "";

export const TOKEN_KEY = "wandor_token";
export const USER_KEY = "wandor_user";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable */
  }
}

export function getStoredUser<T>(): T | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

export function setStoredUser(user: unknown | null) {
  try {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
    else localStorage.removeItem(USER_KEY);
  } catch {
    /* storage unavailable */
  }
}

export class ApiError extends Error {
  status: number;
  code?: string;
  payload?: ApiErrorBody;

  constructor(message: string, status: number, code?: string, payload?: ApiErrorBody) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.payload = payload;
  }
}

function extractMessage(error: AxiosError<ApiErrorBody>): { message: string; code?: string } {
  const payload = error.response?.data;
  if (payload?.detail) {
    const d = payload.detail;
    if (typeof d === "string") {
      return { message: d, code: undefined };
    }
    if (typeof d === "object" && d !== null) {
      const msg = (d as { message?: string }).message ?? (d as { code?: string }).code;
      const code = (d as { code?: string }).code;
      if (msg) return { message: msg, code };
    }
  }
  if (error.code === "ERR_NETWORK") {
    return {
      message: "Cannot reach the backend server. Make sure it is running on the configured host.",
      code: "NETWORK_ERROR",
    };
  }
  if (!error.response) {
    return { message: "Network error. Please check your connection.", code: "NETWORK_ERROR" };
  }
  return {
    message: error.message || "Unexpected error occurred",
    code: `HTTP_${error.response.status}`,
  };
}

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorBody>) => {
    if (axios.isCancel(error)) {
      return Promise.reject(new ApiError("Request cancelled", 0, "CANCELLED"));
    }
    const { message, code } = extractMessage(error);
    const status = error.response?.status ?? 0;

    if (status === 401) {
      setToken(null);
      setStoredUser(null);
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        const redirect = encodeURIComponent(
          window.location.pathname + window.location.search
        );
        window.location.href = `/login?redirect=${redirect}`;
      }
    }

    return Promise.reject(new ApiError(message, status, code, error.response?.data));
  }
);

export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  const res = await api.request<T>(config);
  return res.data;
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  if (error instanceof Error) return new ApiError(error.message, 0, "UNKNOWN");
  return new ApiError("Unknown error", 0, "UNKNOWN");
}

export function errorMessage(error: unknown): string {
  return toApiError(error).message;
}

/** True when the backend is configured to proxy /api to itself (default Vite setup). */
export const USING_PROXY = !import.meta.env.VITE_API_URL || import.meta.env.VITE_API_URL === 'http://localhost:3000';
