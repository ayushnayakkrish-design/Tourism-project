import { request } from "./client";
import type {
  CrowdObservation,
  CrowdForecast,
  SeasonProfile,
  SeasonMonth,
} from "./types";

export const crowdApi = {
  createObservation(data: {
    place_id: string;
    crowd_level: string;
    timestamp?: string;
    source?: string;
    confidence?: number;
  }) {
    return request<CrowdObservation>({ method: "POST", url: "/api/crowd/observations", data });
  },

  getForPlace(placeId: string, options?: { target_hour?: number; target_weekday?: number }) {
    return request<CrowdForecast>({
      method: "GET",
      url: `/api/crowd/${placeId}`,
      params: options,
    });
  },
};

export const seasonApi = {
  createProfile(data: Omit<SeasonProfile, "id" | "overall_score" | "updated_at">) {
    return request<SeasonProfile>({ method: "POST", url: "/api/season/profiles", data });
  },

  getForPlace(placeId: string) {
    return request<{ profiles: SeasonMonth[]; best_month: SeasonMonth | null }>({
      method: "GET",
      url: `/api/season/${placeId}`,
    });
  },
};
