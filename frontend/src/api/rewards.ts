import { request } from "./client";
import type {
  Wallet,
  PointTransaction,
  Reward,
  Redemption,
  RewardAnalytics,
} from "./types";

export const walletApi = {
  get() {
    return request<Wallet>({ method: "GET", url: "/api/wallet" });
  },

  async transactions(params?: { page?: number; page_size?: number }) {
    const data = await request<{ items: PointTransaction[]; total: number; page: number; page_size: number }>({
      method: "GET",
      url: "/api/points/transactions",
      params,
    });
    return { items: data?.items ?? [], total: data?.total ?? 0, page: data?.page ?? 1, page_size: data?.page_size ?? 20 };
  },
};

export const rewardsApi = {
  async list(params?: { available_only?: boolean; category?: string }) {
    const data = await request<{ items: Reward[]; total: number; page: number; page_size: number }>({
      method: "GET",
      url: "/api/rewards",
      params,
    });
    return { items: data?.items ?? [], total: data?.total ?? 0 };
  },

  get(rewardId: number) {
    return request<Reward>({ method: "GET", url: `/api/rewards/${rewardId}` });
  },

  redeem(rewardId: number) {
    return request<Redemption>({ method: "POST", url: `/api/rewards/${rewardId}/redeem` });
  },

  async myRedemptions(params?: { page?: number; page_size?: number }) {
    const data = await request<{ items: Redemption[]; total: number; page: number; page_size: number }>({
      method: "GET",
      url: "/api/redemptions",
      params,
    });
    return { items: data?.items ?? [], total: data?.total ?? 0 };
  },

  getRedemption(redemptionId: number) {
    return request<Redemption>({ method: "GET", url: `/api/redemptions/${redemptionId}` });
  },
};

export const adminRewardsApi = {
  create(data: Omit<Reward, "id" | "status" | "created_at" | "updated_at">) {
    return request<Reward>({ method: "POST", url: "/api/admin/rewards", data });
  },

  update(rewardId: number, data: Partial<Reward>) {
    return request<Reward>({ method: "PATCH", url: `/api/admin/rewards/${rewardId}`, data });
  },

  deactivate(rewardId: number) {
    return request<Reward>({ method: "DELETE", url: `/api/admin/rewards/${rewardId}` });
  },

  allRedemptions(params?: { status?: string; page?: number; page_size?: number }) {
    return request<{ redemptions: Redemption[]; total: number }>({
      method: "GET",
      url: "/api/admin/redemptions",
      params,
    });
  },

  analytics() {
    return request<RewardAnalytics>({ method: "GET", url: "/api/admin/reward-analytics" });
  },

  adjustPoints(userId: string, data: { points: number; reason: string }) {
    return request<unknown>({ method: "POST", url: `/api/admin/users/${userId}/points/adjust`, data });
  },
};
