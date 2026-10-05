import { request } from "./client";
import type {
  PlannerRequest,
  Itinerary,
  ItineraryExplanation,
} from "./types";

export const plannerApi = {
  generate(data: PlannerRequest) {
    return request<Itinerary>({ method: "POST", url: "/api/planner/generate", data });
  },

  explain(itinerary: object) {
    return request<ItineraryExplanation>({ method: "POST", url: "/api/planner/explain", data: { itinerary } });
  },
};
