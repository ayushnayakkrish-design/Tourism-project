import { request, api } from "./client";
import type { AuthResponse, PublicUser, UserPreferences } from "./types";

export const authApi = {
  register(data: { email: string; password: string; display_name: string }) {
    return request<AuthResponse>({ method: "POST", url: "/api/auth/register", data });
  },

  login(data: { email: string; password: string }) {
    return request<AuthResponse>({ method: "POST", url: "/api/auth/login", data });
  },

  me() {
    return request<PublicUser>({ method: "GET", url: "/api/auth/me" });
  },
};

export const usersApi = {
  getProfile() {
    return request<PublicUser>({ method: "GET", url: "/api/users/me" });
  },

  updateProfile(data: Partial<{ display_name: string; bio: string }>) {
    return request<PublicUser>({ method: "PATCH", url: "/api/users/me", data });
  },

  getPreferences() {
    return request<UserPreferences>({ method: "GET", url: "/api/users/me/preferences" });
  },

  updatePreferences(data: Partial<UserPreferences>) {
    return request<UserPreferences>({ method: "PATCH", url: "/api/users/me/preferences", data });
  },

  changePassword(data: { current_password: string; new_password: string }) {
    return request<{ ok: boolean }>({ method: "POST", url: "/api/users/me/password", data });
  },
};

export const adminUsersApi = {
  updateRole(userId: string, data: { role: string }) {
    return request<unknown>({ method: "PATCH", url: `/api/admin/users/${userId}/role`, data });
  },
};
