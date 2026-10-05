import { request, api } from "./client";
import type { Place, PlaceDetails, RouteResponse } from "./types";

export const placesApi = {
  search(q: string, maxResults = 10) {
    return request<{ places: Place[] }>({
      method: "GET",
      url: "/api/places/search",
      params: { q, max_results: maxResults },
    });
  },

  nearby(data: { latitude: number; longitude: number; radius_meters?: number; included_types?: string[] }) {
    return request<{ places: Place[] }>({ method: "POST", url: "/api/places/nearby", data });
  },

  details(placeId: string) {
    return request<PlaceDetails>({ method: "GET", url: `/api/places/details/${placeId}` });
  },

  geocode(address: string) {
    return request<unknown>({ method: "GET", url: "/api/places/geocode", params: { address } });
  },
};

export const routesApi = {
  route(origin: { latitude: number; longitude: number }, destination: { latitude: number; longitude: number }, intermediates?: Array<{ latitude: number; longitude: number }>) {
    return request<RouteResponse>({
      method: "POST",
      url: "/api/routes/route",
      data: { origin, destination, intermediates },
    });
  },

  matrix(origins: Array<{ latitude: number; longitude: number }>, destinations: Array<{ latitude: number; longitude: number }>) {
    return request<unknown>({
      method: "POST",
      url: "/api/routes/matrix",
      data: { origins, destinations },
    });
  },
};
