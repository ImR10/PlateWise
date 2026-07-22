/**
 * Pure, deterministic analytics derivations for the Analysis tab.
 *
 * These functions take mock events as input and never mutate them. Every output
 * is an ESTIMATE derived from mock event counts — nothing here represents
 * confirmed consumption, inventory, or waste. Kept free of React and of the mock
 * data module so it stays unit-testable.
 */
import type {
  AnalysisEvent,
  AnalysisEventType,
  AnalysisSignal,
  DataQuality,
} from "../data/analysisTypes";
import type { FoodCategory, MealPeriod } from "../data/menuTypes";
import { TODAY_ISO, addDaysIso } from "./dates";

export type DateRangePreset = "today" | "last-7" | "last-30" | "custom";
export type ComparisonMode = "previous-period" | "previous-week" | "none";

export interface AnalysisFilters {
  preset: DateRangePreset;
  customStart: string;
  customEnd: string;
  locationId: string | "all";
  mealPeriod: MealPeriod | "all";
  stationId: string | "all";
  category: FoodCategory | "all";
  comparison: ComparisonMode;
}

export interface DateRange {
  start: string;
  end: string;
}

export interface Metrics {
  recommendations: number;
  selections: number;
  confirmed: number;
  dismissed: number;
  unavailable: number;
  selectionRate: number;
}

export interface ItemMetric extends Metrics {
  itemId: string;
}

export interface GroupMetric {
  key: string;
  recommendations: number;
  selections: number;
  selectionRate: number;
}

/** Fraction of recommendation demand assumed prepared (planning estimate). */
export const PREP_FACTOR = 0.7;

export const defaultAnalysisFilters = (): AnalysisFilters => ({
  preset: "last-7",
  customStart: addDaysIso(TODAY_ISO, -6),
  customEnd: TODAY_ISO,
  locationId: "all",
  mealPeriod: "all",
  stationId: "all",
  category: "all",
  comparison: "previous-period",
});

/** Inclusive day count between two ISO dates. */
export const daysBetween = (start: string, end: string): number => {
  const a = new Date(`${start}T00:00:00`);
  const b = new Date(`${end}T00:00:00`);
  return Math.round((b.getTime() - a.getTime()) / 86_400_000);
};

export const dateRangeFor = (
  filters: AnalysisFilters,
  today: string = TODAY_ISO,
): DateRange => {
  switch (filters.preset) {
    case "today":
      return { start: today, end: today };
    case "last-7":
      return { start: addDaysIso(today, -6), end: today };
    case "last-30":
      return { start: addDaysIso(today, -29), end: today };
    case "custom": {
      const start = filters.customStart || today;
      const end = filters.customEnd || today;
      return start <= end ? { start, end } : { start: end, end: start };
    }
  }
};

export const comparisonRangeFor = (
  range: DateRange,
  mode: ComparisonMode,
): DateRange | null => {
  if (mode === "none") return null;
  const length = daysBetween(range.start, range.end) + 1;
  if (mode === "previous-week") {
    return {
      start: addDaysIso(range.start, -7),
      end: addDaysIso(range.end, -7),
    };
  }
  // previous-period: the equally-long window immediately before the range.
  const end = addDaysIso(range.start, -1);
  return { start: addDaysIso(end, -(length - 1)), end };
};

const inRange = (date: string, range: DateRange): boolean =>
  date >= range.start && date <= range.end;

const matchesFilters = (
  event: AnalysisEvent,
  filters: AnalysisFilters,
): boolean => {
  if (filters.locationId !== "all" && event.locationId !== filters.locationId)
    return false;
  if (filters.mealPeriod !== "all" && event.mealPeriod !== filters.mealPeriod)
    return false;
  if (filters.stationId !== "all" && event.stationId !== filters.stationId)
    return false;
  if (filters.category !== "all" && event.category !== filters.category)
    return false;
  return true;
};

/** Events within a date range and matching the categorical filters. */
export const selectEvents = (
  events: AnalysisEvent[],
  filters: AnalysisFilters,
  range: DateRange,
): AnalysisEvent[] =>
  events.filter(
    (event) => inRange(event.date, range) && matchesFilters(event, filters),
  );

export const sumByType = (
  events: AnalysisEvent[],
  type: AnalysisEventType,
): number =>
  events.reduce((n, e) => (e.eventType === type ? n + e.quantity : n), 0);

export const selectionRate = (
  selections: number,
  recommendations: number,
): number => (recommendations > 0 ? selections / recommendations : 0);

export const computeMetrics = (events: AnalysisEvent[]): Metrics => {
  const recommendations = sumByType(events, "recommendation-shown");
  const selections = sumByType(events, "item-selected");
  return {
    recommendations,
    selections,
    confirmed: sumByType(events, "selection-confirmed"),
    dismissed: sumByType(events, "recommendation-dismissed"),
    unavailable: sumByType(events, "item-unavailable"),
    selectionRate: selectionRate(selections, recommendations),
  };
};

const groupBy = <K extends string>(
  events: AnalysisEvent[],
  keyFn: (e: AnalysisEvent) => K,
): Map<K, AnalysisEvent[]> => {
  const map = new Map<K, AnalysisEvent[]>();
  for (const event of events) {
    const key = keyFn(event);
    const list = map.get(key);
    if (list) list.push(event);
    else map.set(key, [event]);
  }
  return map;
};

export const itemMetrics = (events: AnalysisEvent[]): ItemMetric[] =>
  [...groupBy(events, (e) => e.foodItemId).entries()]
    .map(([itemId, list]) => ({ itemId, ...computeMetrics(list) }))
    .sort((a, b) => b.recommendations - a.recommendations);

const groupMetric = (
  events: AnalysisEvent[],
  keyFn: (e: AnalysisEvent) => string,
): GroupMetric[] =>
  [...groupBy(events, keyFn).entries()]
    .map(([key, list]) => {
      const m = computeMetrics(list);
      return {
        key,
        recommendations: m.recommendations,
        selections: m.selections,
        selectionRate: m.selectionRate,
      };
    })
    .sort((a, b) => b.recommendations - a.recommendations);

export const byLocation = (events: AnalysisEvent[]): GroupMetric[] =>
  groupMetric(events, (e) => e.locationId);
export const byMealPeriod = (events: AnalysisEvent[]): GroupMetric[] =>
  groupMetric(events, (e) => e.mealPeriod);
export const byStation = (events: AnalysisEvent[]): GroupMetric[] =>
  groupMetric(events, (e) => e.stationId);
export const byCategory = (events: AnalysisEvent[]): GroupMetric[] =>
  groupMetric(events, (e) => e.category);

export const topRecommendedItems = (
  events: AnalysisEvent[],
  n: number,
): ItemMetric[] => itemMetrics(events).slice(0, n);

/** Estimated prepared servings for an item (planning estimate from demand). */
export const estimatedPrepared = (recommendations: number): number =>
  Math.round(recommendations * PREP_FACTOR);

export const estimatedUnused = (
  recommendations: number,
  selections: number,
): number => Math.max(0, estimatedPrepared(recommendations) - selections);

export interface ItemComparison {
  itemId: string;
  current: ItemMetric;
  previous?: ItemMetric;
  recsChangePct: number | null;
  selChangePct: number | null;
}

const changePct = (current: number, previous: number): number | null =>
  previous > 0 ? (current - previous) / previous : null;

export const itemComparisons = (
  currentEvents: AnalysisEvent[],
  previousEvents: AnalysisEvent[] | null,
): ItemComparison[] => {
  const current = itemMetrics(currentEvents);
  const prevById = new Map(
    (previousEvents ? itemMetrics(previousEvents) : []).map((m) => [
      m.itemId,
      m,
    ]),
  );
  return current.map((m) => {
    const previous = prevById.get(m.itemId);
    return {
      itemId: m.itemId,
      current: m,
      previous,
      recsChangePct: previous
        ? changePct(m.recommendations, previous.recommendations)
        : null,
      selChangePct: previous
        ? changePct(m.selections, previous.selections)
        : null,
    };
  });
};

export type TrendDirection = "up" | "down" | "flat" | "unknown";

export const trendDirection = (pct: number | null): TrendDirection => {
  if (pct === null) return "unknown";
  if (pct > 0.1) return "up";
  if (pct < -0.1) return "down";
  return "flat";
};

export const risingItems = (comparisons: ItemComparison[]): ItemComparison[] =>
  comparisons
    .filter((c) => trendDirection(c.recsChangePct) === "up")
    .sort((a, b) => (b.recsChangePct ?? 0) - (a.recsChangePct ?? 0));

export const fallingItems = (comparisons: ItemComparison[]): ItemComparison[] =>
  comparisons
    .filter((c) => trendDirection(c.recsChangePct) === "down")
    .sort((a, b) => (a.recsChangePct ?? 0) - (b.recsChangePct ?? 0));

export interface UnmetDemandItem {
  itemId: string;
  locationId: string;
  mealPeriod: string;
  recommendations: number;
  unavailableEvents: number;
  estimatedMissedSelections: number;
}

/** Items recommended while unavailable, with an estimate of missed selections. */
export const unavailableHighDemandItems = (
  events: AnalysisEvent[],
): UnmetDemandItem[] => {
  const byItem = groupBy(events, (e) => e.foodItemId);
  const result: UnmetDemandItem[] = [];
  for (const [itemId, list] of byItem.entries()) {
    const unavailable = sumByType(list, "item-unavailable");
    if (unavailable <= 0) continue;
    const m = computeMetrics(list);
    const sample = list[0];
    result.push({
      itemId,
      locationId: sample.locationId,
      mealPeriod: sample.mealPeriod,
      recommendations: m.recommendations,
      unavailableEvents: unavailable,
      estimatedMissedSelections: Math.round(unavailable * m.selectionRate),
    });
  }
  return result.sort((a, b) => b.unavailableEvents - a.unavailableEvents);
};

export const dataQualityFor = (recommendations: number): DataQuality => {
  if (recommendations >= 400) return "high";
  if (recommendations >= 80) return "medium";
  return "low";
};

const LOW_VOLUME = 30;

/** Advisory operational signals derived from item metrics + comparison. */
export const buildSignals = (
  currentEvents: AnalysisEvent[],
  previousEvents: AnalysisEvent[] | null,
): AnalysisSignal[] => {
  const comparisons = itemComparisons(currentEvents, previousEvents);
  const byItemEvents = groupBy(currentEvents, (e) => e.foodItemId);
  const signals: AnalysisSignal[] = [];

  for (const c of comparisons) {
    const m = c.current;
    const events = byItemEvents.get(m.itemId) ?? [];
    const location = events[0]?.locationId;
    const quality = dataQualityFor(m.recommendations);
    const prepared = estimatedPrepared(m.recommendations);
    const unused = estimatedUnused(m.recommendations, m.selections);
    const ratePct = `${Math.round(m.selectionRate * 100)}%`;

    if (m.recommendations < LOW_VOLUME) {
      signals.push({
        id: `sig-${m.itemId}-insufficient`,
        type: "insufficient-data",
        severity: "info",
        foodItemId: m.itemId,
        locationId: location,
        reason:
          "Too few recommendations in this range for a reliable estimate.",
        interpretation:
          "Suggested review — widen the date range or wait for more mock events.",
        dataQuality: quality,
        metrics: [
          { label: "Recommendations", value: String(m.recommendations) },
          { label: "Estimated selections", value: String(m.selections) },
        ],
      });
      continue;
    }

    if (m.unavailable > 0) {
      signals.push({
        id: `sig-${m.itemId}-shortage`,
        type: "shortage-risk",
        severity: "risk",
        foodItemId: m.itemId,
        locationId: location,
        reason: "Recommended while marked unavailable — possible unmet demand.",
        interpretation: "Consider preparing more or improving availability.",
        dataQuality: quality,
        metrics: [
          { label: "Recommendations", value: String(m.recommendations) },
          { label: "Unavailable events", value: String(m.unavailable) },
          {
            label: "Estimated missed selections",
            value: String(Math.round(m.unavailable * m.selectionRate)),
          },
        ],
      });
    }

    if (m.selectionRate < 0.2) {
      signals.push({
        id: `sig-${m.itemId}-overproduction`,
        type: "overproduction-risk",
        severity: "risk",
        foodItemId: m.itemId,
        locationId: location,
        reason:
          "Low estimated selection rate relative to recommendation demand.",
        interpretation: "Consider reducing preparation for this item.",
        dataQuality: quality,
        metrics: [
          { label: "Estimated selection rate", value: ratePct },
          { label: "Estimated prepared servings", value: String(prepared) },
          { label: "Estimated unused servings", value: String(unused) },
        ],
      });
    } else {
      const dir = trendDirection(c.recsChangePct);
      if (dir === "up") {
        signals.push({
          id: `sig-${m.itemId}-increasing`,
          type: "demand-increasing",
          severity: "watch",
          foodItemId: m.itemId,
          locationId: location,
          reason: "Projected demand rising versus the comparison period.",
          interpretation: "Consider preparing more.",
          dataQuality: quality,
          metrics: [
            {
              label: "Recommendations change",
              value: `${Math.round((c.recsChangePct ?? 0) * 100)}%`,
            },
          ],
        });
      } else if (dir === "down") {
        signals.push({
          id: `sig-${m.itemId}-decreasing`,
          type: "demand-decreasing",
          severity: "watch",
          foodItemId: m.itemId,
          locationId: location,
          reason: "Projected demand falling versus the comparison period.",
          interpretation: "Consider reducing preparation.",
          dataQuality: quality,
          metrics: [
            {
              label: "Recommendations change",
              value: `${Math.round((c.recsChangePct ?? 0) * 100)}%`,
            },
          ],
        });
      } else {
        signals.push({
          id: `sig-${m.itemId}-stable`,
          type: "stable-demand",
          severity: "info",
          foodItemId: m.itemId,
          locationId: location,
          reason: "Estimated demand is steady versus the comparison period.",
          interpretation: "No preparation change suggested.",
          dataQuality: quality,
          metrics: [
            { label: "Recommendations", value: String(m.recommendations) },
            { label: "Estimated selection rate", value: ratePct },
          ],
        });
      }
    }
  }

  return signals;
};
