export type Role =
  | "TOURIST"
  | "CONTRIBUTOR"
  | "MODERATOR"
  | "GOVERNMENT_ADMIN"
  | "SUPER_ADMIN";

export interface CurrentUser {
  user_id: string;
  role: Role;
  email?: string | null;
  display_name?: string | null;
}

export interface PublicUser {
  id: string;
  email: string;
  display_name: string;
  bio: string;
  role: Role;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: PublicUser;
}

export interface UserPreferences {
  language: string;
  theme: string;
  voice_enabled: boolean;
  units: string;
}

export interface Place {
  place_id: string;
  name: string;
  latitude: number;
  longitude: number;
  type: string | null;
  types: string[];
  address: string | null;
  map_url: string | null;
}

export interface PlaceDetails extends Place {
  rating?: number | null;
  user_ratings_total?: number | null;
  price_level?: string | null;
  opening_hours?: unknown;
  accessibility?: unknown;
  photos?: string[];
  reviews?: unknown[];
}

export interface RouteStep {
  duration_seconds?: number;
  distance_meters?: number;
  static_duration_seconds?: number;
  travel_mode?: string;
  localized_values?: Record<string, unknown>;
  [k: string]: unknown;
}

export interface RouteResponse {
  routes?: Array<{
    legs?: Array<{
      distance_meters?: number;
      duration_seconds?: number;
      static_duration_seconds?: number;
      steps?: RouteStep[];
      [k: string]: unknown;
    }>;
    [k: string]: unknown;
  }>;
  [k: string]: unknown;
}

export interface CrowdObservation {
  id: number;
  place_id: string;
  timestamp: string;
  crowd_level: string;
  source: string;
  confidence: number;
}

export interface CrowdForecast {
  predicted_level?: string;
  confidence?: number;
  sample_count?: number;
  hour?: number;
  best_time_slots?: Array<{
    hour: number;
    predicted_level: string;
    confidence: number;
    sample_count: number;
    [k: string]: unknown;
  }>;
  [k: string]: unknown;
}

export interface SeasonProfile {
  id?: number;
  place_id: string;
  month: number;
  weather_score: number;
  crowd_score: number;
  festival_score: number;
  accessibility_score: number;
  overall_score: number;
  reason?: string | null;
  updated_at?: string;
}

export interface SeasonMonth extends SeasonProfile {
  month_name?: string;
}

export interface PlannerPreferences {
  temples: boolean;
  nature: boolean;
  food: boolean;
  beaches: boolean;
  culture: boolean;
  shopping: boolean;
  adventure: boolean;
  family_friendly: boolean;
  [k: string]: boolean;
}

export interface PlannerRequest {
  start_location: { latitude: number; longitude: number };
  destinations: string[];
  available_hours: number;
  days: number;
  start_time: string;
  start_date?: string;
  visit_duration_minutes?: number;
  return_to_start?: boolean;
  preferences: PlannerPreferences;
}

export interface ItineraryPlace {
  place_id: string;
  name: string;
  latitude: number;
  longitude: number;
  types: string[];
  opening_hours?: unknown;
  accessibility?: unknown;
  crowd_level?: string | null;
  crowd_confidence?: number | null;
  preference_score?: number;
  [k: string]: unknown;
}

export interface TravelSegment {
  from: string;
  to: string;
  duration_seconds: number;
  distance_meters: number;
  travel_mode?: string;
  [k: string]: unknown;
}

export interface ItineraryDay {
  day: number;
  items: Array<{
    place: ItineraryPlace;
    start: string;
    end: string;
    duration_minutes: number;
    travel_in_seconds?: number;
    travel_in_meters?: number;
    opening_status?: string;
    crowd_level?: string | null;
    reasoning?: string | null;
    [k: string]: unknown;
  }>;
  return_leg_seconds?: number | null;
  return_leg_meters?: number | null;
  total_place_minutes?: number;
  total_travel_minutes?: number;
  [k: string]: unknown;
}

export interface Itinerary {
  days: ItineraryDay[];
  estimated_total_duration_minutes?: number;
  estimated_total_distance_meters?: number;
  origin: { latitude: number; longitude: number };
  [k: string]: unknown;
}

export interface ItineraryExplanation {
  enabled: boolean;
  explanation: string;
  model?: string | null;
}

export interface Visit {
  id: number;
  user_id: string;
  place_id: string;
  latitude: number;
  longitude: number;
  timestamp: string;
  status: string;
  verification_method: string | null;
  verification_radius: number | null;
  distance_from_place: number | null;
  rejection_reason: string | null;
  anti_cheat_reasons: string[] | null;
  visit_reward_granted: boolean;
  visit_points_awarded: number | null;
  created_at?: string;
  [k: string]: unknown;
}

export interface VisitProof {
  id: number;
  visit_id: number;
  storage_url: string;
  verification_status: string;
  rejection_reason: string | null;
  reward_granted: boolean;
  points_awarded: number | null;
  created_at?: string;
  [k: string]: unknown;
}

export interface Wallet {
  user_id: string;
  balance: number;
  lifetime_points_earned: number;
  lifetime_points_spent: number;
  [k: string]: unknown;
}

export interface PointTransaction {
  id: number;
  user_id: string;
  transaction_type: string;
  points: number;
  balance_after: number | null;
  reference: string | null;
  description: string | null;
  created_at: string;
  [k: string]: unknown;
}

export interface Paginated<T> {
  items?: T[];
  total?: number;
  page?: number;
  page_size?: number;
  [k: string]: unknown;
}

export interface Reward {
  id: number;
  name: string;
  description: string;
  provider: string;
  category: string;
  points_required: number;
  stock: number | null;
  max_stock?: number | null;
  status: string;
  expires_at: string | null;
  created_at?: string;
  updated_at?: string | null;
  [k: string]: unknown;
}

export interface Redemption {
  id: number;
  user_id: string;
  reward_id: number;
  reward_name?: string;
  points_spent: number;
  redemption_code: string;
  status: string;
  created_at: string;
  [k: string]: unknown;
}

export interface RewardAnalytics {
  total_redemptions: number;
  total_points_spent: number;
  redemptions_by_reward?: Array<{ reward_id: number; reward_name: string; count: number; points: number }>;
  redemptions_by_status?: Array<{ status: string; count: number }>;
  top_rewards?: Array<{ reward_id: number; reward_name: string; count: number }>;
  [k: string]: unknown;
}

export interface CommunitySubmission {
  id: string;
  user_id: string;
  type: string;
  name: string;
  latitude: number;
  longitude: number;
  description: string;
  photos: string[];
  language: string;
  status: string;
  moderator_note: string | null;
  created_at: string;
  [k: string]: unknown;
}

export interface Review {
  id: string;
  user_id: string;
  place_id: string;
  rating: number;
  comment: string;
  status: string;
  created_at: string;
  [k: string]: unknown;
}

export interface ModerationHistoryEntry {
  id: string;
  moderator_id: string;
  target_type: string;
  target_id: string;
  action: string;
  reason: string | null;
  created_at: string;
  [k: string]: unknown;
}

export interface PlaceContent {
  place_id: string;
  language: string;
  title: string;
  description: string;
  rules?: string | null;
  tips?: string | null;
  source: string;
  updated_at?: string;
}

export interface TranslationResponse {
  text: string;
  source_language: string;
  target_language: string;
  cached: boolean;
}

export interface IntentParameters {
  category?: string | null;
  location?: string | null;
  open_now?: boolean;
  query: string;
}

export interface IntentResult {
  intent: string;
  parameters: IntentParameters;
}

export interface VoiceResponse {
  intent?: string;
  parameters?: IntentParameters;
  transcription?: string | null;
  places?: Place[];
  [k: string]: unknown;
}

export interface ApiErrorBody {
  detail?: string | { code?: string; message?: string; [k: string]: unknown };
  [k: string]: unknown;
}

export const MODERATOR_ROLES: Role[] = ["MODERATOR", "GOVERNMENT_ADMIN", "SUPER_ADMIN"];
export const ADMIN_ROLES: Role[] = ["GOVERNMENT_ADMIN", "SUPER_ADMIN"];

export function isModerator(role?: Role | null) {
  return !!role && MODERATOR_ROLES.includes(role);
}

export function isAdmin(role?: Role | null) {
  return !!role && ADMIN_ROLES.includes(role);
}

export const SUPPORTED_LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "or", label: "ଓଡ଼ିଆ" },
] as const;

export const LANGUAGE_LABEL: Record<string, string> = {
  en: "English",
  hi: "हिन्दी",
  or: "ଓଡ଼ିଆ",
};
