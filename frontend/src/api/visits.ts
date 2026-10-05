import { request, api } from "./client";
import type { Visit, VisitProof } from "./types";

export const visitsApi = {
  create(data: { place_id: string; latitude: number; longitude: number; timestamp: string }) {
    return request<Visit>({ method: "POST", url: "/api/visits", data });
  },

  async list(params?: { status?: string; page?: number; page_size?: number }) {
    const data = await request<{ items: Visit[]; total: number; page: number; page_size: number }>({
      method: "GET",
      url: "/api/visits",
      params,
    });
    return { items: data?.items ?? [], total: data?.total ?? 0 };
  },

  get(visitId: number) {
    return request<Visit>({ method: "GET", url: `/api/visits/${visitId}` });
  },

  uploadProof(visitId: number, file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<VisitProof>(`/api/visits/${visitId}/proof`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then(r => r.data);
  },
};
