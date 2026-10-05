import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPoints(n: number) {
  return new Intl.NumberFormat().format(n);
}

export function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

export function formatDuration(minutes?: number | null) {
  if (minutes == null) return "—";
  if (minutes < 60) return `${Math.round(minutes)}m`;
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  return m ? `${h}h ${m}m` : `${h}h`;
}

export function timeSlotOf(hour: number) {
  if (hour < 12) return "Morning";
  if (hour < 17) return "Afternoon";
  return "Evening";
}

export const CROWD_LEVELS = ["VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH"] as const;
export type CrowdLevel = (typeof CROWD_LEVELS)[number];

export const CROWD_META: Record<CrowdLevel, { label: string; color: string; bg: string; dot: string }> = {
  VERY_LOW: { label: "Very Low", color: "text-emerald-700", bg: "bg-emerald-500/15", dot: "bg-emerald-500" },
  LOW: { label: "Low", color: "text-emerald-600", bg: "bg-emerald-400/15", dot: "bg-emerald-400" },
  MODERATE: { label: "Moderate", color: "text-amber-700", bg: "bg-amber-400/20", dot: "bg-amber-400" },
  HIGH: { label: "High", color: "text-orange-700", bg: "bg-orange-500/20", dot: "bg-orange-500" },
  VERY_HIGH: { label: "Very High", color: "text-red-700", bg: "bg-red-500/20", dot: "bg-red-500" },
};

export function crowdMeta(level: string) {
  const key = (level || "MODERATE").toUpperCase() as CrowdLevel;
  return CROWD_META[key] ?? CROWD_META.MODERATE;
}

export function scoreColor(score: number) {
  if (score >= 80) return "text-emerald-600";
  if (score >= 60) return "text-amber-600";
  return "text-red-600";
}

export function scoreBarColor(score: number) {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 60) return "bg-amber-500";
  return "bg-red-500";
}
