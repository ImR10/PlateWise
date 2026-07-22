/**
 * Deterministic mock analytics events for the Analysis tab.
 *
 * Events are generated from a small, readable per-item profile table so the
 * derived metrics are stable and unit-testable. Everything is an ESTIMATE built
 * from mock event counts — there is no real ingestion, POS, or inventory data.
 * Food-item / location / category IDs match the managed records elsewhere.
 */
import { TODAY_ISO, addDaysIso } from "../lib/dates";
import type { FoodCategory, MealPeriod } from "./menuTypes";
import type {
  AnalysisEvent,
  AnalysisEventType,
  DataSourceRow,
} from "./analysisTypes";

/**
 * Future data sources that would power real analytics. Only menu publication,
 * recommendation events, and availability events exist as frontend mock model;
 * everything measuring physical consumption or inventory requires integration.
 */
export const dataSources: DataSourceRow[] = [
  {
    id: "menu-publication",
    label: "Menu publication data",
    status: "frontend-model",
    enables: "Which items were offered, where, and when.",
  },
  {
    id: "recommendation-events",
    label: "Recommendation events",
    status: "mock-data",
    enables: "How often items are recommended (demand signal).",
  },
  {
    id: "selection-confirmations",
    label: "Student selection confirmations",
    status: "backend-required",
    enables: "Estimated selections and selection-rate accuracy.",
  },
  {
    id: "availability-events",
    label: "Item availability events",
    status: "mock-data",
    enables: "Unmet demand and possible shortage risk.",
  },
  {
    id: "servings-prepared",
    label: "Servings prepared",
    status: "integration-required",
    enables: "Preparation vs demand and overproduction risk.",
  },
  {
    id: "servings-taken",
    label: "Servings taken",
    status: "not-connected",
    enables: "Confirmed selections and unused-serving estimates.",
  },
  {
    id: "leftover-records",
    label: "Leftover or waste records",
    status: "not-connected",
    enables: "Measured waste analytics.",
  },
  {
    id: "inventory-system",
    label: "Inventory system",
    status: "integration-required",
    enables: "Stock levels and shortage forecasting.",
  },
  {
    id: "pos-system",
    label: "Point-of-sale system",
    status: "not-connected",
    enables: "Confirmed transaction and consumption counts.",
  },
];

/** The window of mock history, ending on the app's fixed "today". */
export const ANALYSIS_DAYS = 30;
export const ANALYSIS_TODAY = TODAY_ISO;
/** Deterministic "last updated" label (mock). */
export const ANALYSIS_LAST_UPDATED = "Today at 6:00 AM";

interface ItemProfile {
  foodItemId: string;
  locationId: string;
  mealPeriod: MealPeriod;
  stationId: string;
  category: FoodCategory;
  /** Baseline recommendations shown per day. */
  recsPerDay: number;
  /** Estimated fraction of recommendations that lead to a selection. */
  selectionRate: number;
  trend: "flat" | "rising" | "falling";
  /** Whether the item periodically goes unavailable while in demand. */
  unavailable: boolean;
}

// Categories intentionally mirror the managed Food Catalog seed.
const PROFILES: ItemProfile[] = [
  {
    foodItemId: "cat-01",
    locationId: "loc-a",
    mealPeriod: "lunch",
    stationId: "stn-a",
    category: "Category A",
    recsPerDay: 45,
    selectionRate: 0.55,
    trend: "flat",
    unavailable: false,
  },
  {
    foodItemId: "cat-02",
    locationId: "loc-a",
    mealPeriod: "breakfast",
    stationId: "stn-b",
    category: "Category A",
    recsPerDay: 30,
    selectionRate: 0.5,
    trend: "rising",
    unavailable: false,
  },
  {
    foodItemId: "cat-03",
    locationId: "loc-b",
    mealPeriod: "dinner",
    stationId: "stn-a",
    category: "Category B",
    recsPerDay: 28,
    selectionRate: 0.48,
    trend: "falling",
    unavailable: false,
  },
  {
    foodItemId: "cat-04",
    locationId: "loc-b",
    mealPeriod: "lunch",
    stationId: "stn-c",
    category: "Category B",
    recsPerDay: 20,
    selectionRate: 0.6,
    trend: "flat",
    unavailable: false,
  },
  {
    foodItemId: "cat-05",
    locationId: "loc-c",
    mealPeriod: "dinner",
    stationId: "stn-a",
    category: "Category C",
    recsPerDay: 25,
    selectionRate: 0.5,
    trend: "flat",
    unavailable: true,
  },
  {
    foodItemId: "cat-06",
    locationId: "loc-c",
    mealPeriod: "lunch",
    stationId: "stn-b",
    category: "Category C",
    recsPerDay: 15,
    selectionRate: 0.45,
    trend: "flat",
    unavailable: false,
  },
  {
    foodItemId: "cat-07",
    locationId: "loc-d",
    mealPeriod: "dinner",
    stationId: "stn-a",
    category: "Category D",
    recsPerDay: 35,
    selectionRate: 0.12,
    trend: "flat",
    unavailable: false,
  },
  {
    foodItemId: "cat-08",
    locationId: "loc-d",
    mealPeriod: "lunch",
    stationId: "stn-b",
    category: "Category D",
    recsPerDay: 12,
    selectionRate: 0.5,
    trend: "flat",
    unavailable: false,
  },
  {
    foodItemId: "cat-09",
    locationId: "loc-e",
    mealPeriod: "breakfast",
    stationId: "stn-a",
    category: "Category A",
    recsPerDay: 10,
    selectionRate: 0.7,
    trend: "flat",
    unavailable: false,
  },
  {
    foodItemId: "cat-10",
    locationId: "loc-e",
    mealPeriod: "lunch",
    stationId: "stn-c",
    category: "Category B",
    recsPerDay: 8,
    selectionRate: 0.4,
    trend: "flat",
    unavailable: false,
  },
  {
    foodItemId: "cat-11",
    locationId: "loc-a",
    mealPeriod: "dinner",
    stationId: "stn-d",
    category: "Category C",
    recsPerDay: 5,
    selectionRate: 0.5,
    trend: "flat",
    unavailable: false,
  },
  {
    foodItemId: "cat-12",
    locationId: "loc-b",
    mealPeriod: "breakfast",
    stationId: "stn-e",
    category: "Category D",
    recsPerDay: 18,
    selectionRate: 0.5,
    trend: "flat",
    unavailable: false,
  },
];

const dayFactor = (dayIndex: number, trend: ItemProfile["trend"]): number => {
  const t = dayIndex / (ANALYSIS_DAYS - 1); // 0 (oldest) → 1 (today)
  if (trend === "rising") return 0.55 + 0.45 * t;
  if (trend === "falling") return 1 - 0.45 * t;
  return 1;
};

function generateEvents(): AnalysisEvent[] {
  const events: AnalysisEvent[] = [];
  const push = (
    p: ItemProfile,
    date: string,
    eventType: AnalysisEventType,
    quantity: number,
  ) => {
    if (quantity <= 0) return;
    events.push({
      id: `ev-${p.foodItemId}-${date}-${eventType}`,
      date,
      locationId: p.locationId,
      mealPeriod: p.mealPeriod,
      stationId: p.stationId,
      foodItemId: p.foodItemId,
      category: p.category,
      eventType,
      quantity,
    });
  };

  for (let i = 0; i < ANALYSIS_DAYS; i += 1) {
    const date = addDaysIso(ANALYSIS_TODAY, -(ANALYSIS_DAYS - 1 - i));
    for (const p of PROFILES) {
      const recs = Math.round(p.recsPerDay * dayFactor(i, p.trend));
      const selected = Math.round(recs * p.selectionRate);
      const confirmed = Math.round(selected * 0.9);
      const dismissed = Math.max(0, recs - selected);
      push(p, date, "recommendation-shown", recs);
      push(p, date, "item-selected", selected);
      push(p, date, "selection-confirmed", confirmed);
      push(p, date, "recommendation-dismissed", dismissed);
      if (p.unavailable && i % 4 === 0) {
        push(p, date, "item-unavailable", 3);
      }
    }
  }
  return events;
}

export const analysisEvents: AnalysisEvent[] = generateEvents();
