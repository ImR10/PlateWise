/**
 * Typed analytics domain for the frontend-only Analysis tab.
 *
 * IMPORTANT: everything here is generic MOCK data. There is no analytics
 * ingestion, no point-of-sale, no inventory backend, and no student tracking.
 * Consumption, prepared-serving, and waste figures are ESTIMATES derived from
 * mock event counts — never confirmed measurements. See `lib/analysis.ts` for
 * the deterministic derivations. Food-item and dining-location IDs match the
 * managed Food Catalog / Dining Locations records so the page stays consistent.
 */
import type { FoodCategory, MealPeriod } from "./menuTypes";

export type AnalysisEventType =
  | "recommendation-shown"
  | "item-selected"
  | "selection-confirmed"
  | "recommendation-dismissed"
  | "item-unavailable";

/** One aggregated mock analytics event (a count for a day/slot/item). */
export interface AnalysisEvent {
  id: string;
  date: string; // ISO calendar date, YYYY-MM-DD
  locationId: string;
  mealPeriod: MealPeriod;
  stationId: string;
  foodItemId: string;
  category: FoodCategory;
  eventType: AnalysisEventType;
  quantity: number;
}

/** Generic analysis stations (not tied to a single dining location). */
export const ANALYSIS_STATIONS: { id: string; label: string }[] = [
  { id: "stn-a", label: "Station A" },
  { id: "stn-b", label: "Station B" },
  { id: "stn-c", label: "Station C" },
  { id: "stn-d", label: "Station D" },
  { id: "stn-e", label: "Station E" },
];

export const stationLabel = (id: string): string =>
  ANALYSIS_STATIONS.find((s) => s.id === id)?.label ?? id;

/** Future data sources that would power real analytics, and their status. */
export type DataSourceStatus =
  | "mock-data"
  | "frontend-model"
  | "not-connected"
  | "integration-required"
  | "backend-required";

export interface DataSourceRow {
  id: string;
  label: string;
  status: DataSourceStatus;
  enables: string;
}

export const DATA_SOURCE_STATUS_LABEL: Record<DataSourceStatus, string> = {
  "mock-data": "Mock data",
  "frontend-model": "Available in frontend model",
  "not-connected": "Not connected",
  "integration-required": "Integration required",
  "backend-required": "Backend required",
};

/** Advisory operational-signal kinds. Never presented as commands. */
export type SignalType =
  | "prepare-more"
  | "prepare-less"
  | "demand-increasing"
  | "demand-decreasing"
  | "stable-demand"
  | "shortage-risk"
  | "overproduction-risk"
  | "high-demand-unavailable"
  | "low-selection-high-recs"
  | "insufficient-data";

export type SignalSeverity = "info" | "watch" | "risk";

export type DataQuality = "high" | "medium" | "low";

export interface AnalysisSignal {
  id: string;
  type: SignalType;
  severity: SignalSeverity;
  foodItemId: string;
  locationId?: string;
  reason: string;
  interpretation: string;
  dataQuality: DataQuality;
  metrics: { label: string; value: string }[];
}

export const SIGNAL_TYPE_LABEL: Record<SignalType, string> = {
  "prepare-more": "Consider preparing more",
  "prepare-less": "Consider reducing preparation",
  "demand-increasing": "Demand increasing",
  "demand-decreasing": "Demand decreasing",
  "stable-demand": "Stable demand",
  "shortage-risk": "Possible shortage risk",
  "overproduction-risk": "Possible overproduction risk",
  "high-demand-unavailable": "High demand while unavailable",
  "low-selection-high-recs": "Low selection despite high recommendations",
  "insufficient-data": "Insufficient data",
};

export const SEVERITY_LABEL: Record<SignalSeverity, string> = {
  info: "Info",
  watch: "Watch",
  risk: "Possible risk",
};

export const DATA_QUALITY_LABEL: Record<DataQuality, string> = {
  high: "Higher-confidence estimate",
  medium: "Medium-confidence estimate",
  low: "Low-confidence estimate",
};
