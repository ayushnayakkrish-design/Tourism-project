import { request } from "./client";
import type { PlaceContent, TranslationResponse, IntentResult, VoiceResponse } from "./types";

export const localizationApi = {
  getContent(placeId: string, language: string) {
    return request<PlaceContent>({
      method: "GET",
      url: `/api/localization/${placeId}/content/${language}`,
    });
  },

  upsertContent(data: {
    place_id: string;
    language: string;
    title: string;
    description: string;
    rules?: string;
    tips?: string;
    source: string;
  }) {
    return request<PlaceContent>({ method: "PUT", url: "/api/localization/content", data });
  },

  translate(data: { text: string; source_language: string; target_language: string }) {
    return request<TranslationResponse>({ method: "POST", url: "/api/translate", data });
  },
};

export const voiceApi = {
  textQuery(data: { query: string; language?: string }) {
    return request<VoiceResponse>({ method: "POST", url: "/api/voice/query", data });
  },

  audioQuery(data: { audio_base64: string; language?: string }) {
    return request<VoiceResponse>({ method: "POST", url: "/api/voice/audio", data });
  },
};

export const aiApi = {
  intent(data: { query: string }) {
    return request<IntentResult>({ method: "POST", url: "/api/ai/intent", data });
  },
};
