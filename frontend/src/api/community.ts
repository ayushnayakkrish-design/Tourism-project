import { request } from "./client";
import type {
  CommunitySubmission,
  Review,
  ModerationHistoryEntry,
} from "./types";

export const communityApi = {
  createSubmission(data: {
    type: string;
    name: string;
    latitude: number;
    longitude: number;
    description: string;
    photos: string[];
    language: string;
  }) {
    return request<CommunitySubmission>({ method: "POST", url: "/api/community/places", data });
  },

  listSubmissions(params?: { page?: number; page_size?: number }) {
    return request<CommunitySubmission[]>({ method: "GET", url: "/api/community/places", params });
  },

  getSubmission(id: string) {
    return request<CommunitySubmission>({ method: "GET", url: `/api/community/places/${id}` });
  },

  mySubmissions() {
    return request<CommunitySubmission[]>({ method: "GET", url: "/api/community/places/mine" });
  },

  createReview(data: { place_id: string; rating: number; comment: string }) {
    return request<Review>({ method: "POST", url: "/api/community/reviews", data });
  },

  listReviews(placeId: string) {
    return request<Review[]>({ method: "GET", url: `/api/places/${placeId}/reviews` });
  },
};

export const moderationApi = {
  queue() {
    return request<{ submissions: CommunitySubmission[]; reviews: Review[] }>({
      method: "GET",
      url: "/api/moderation/queue",
    });
  },

  history(params?: { target_type?: string; page?: number; page_size?: number }) {
    return request<ModerationHistoryEntry[]>({ method: "GET", url: "/api/moderation/history", params });
  },

  approveSubmission(id: string, note?: string) {
    return request<CommunitySubmission>({
      method: "POST",
      url: `/api/moderation/submissions/${id}/approve`,
      data: { note: note ?? "" },
    });
  },

  rejectSubmission(id: string, reason: string) {
    return request<CommunitySubmission>({
      method: "POST",
      url: `/api/moderation/submissions/${id}/reject`,
      data: { reason },
    });
  },

  approveReview(id: string) {
    return request<Review>({ method: "POST", url: `/api/moderation/reviews/${id}/approve` });
  },

  rejectReview(id: string, reason: string) {
    return request<Review>({
      method: "POST",
      url: `/api/moderation/reviews/${id}/reject`,
      data: { reason },
    });
  },
};
