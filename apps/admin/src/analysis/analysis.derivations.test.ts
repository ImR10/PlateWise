import { describe, expect, it } from "vitest";

import { analysisEvents } from "../data/analysis";
import { TODAY_ISO, addDaysIso } from "../lib/dates";
import {
  buildSignals,
  byLocation,
  comparisonRangeFor,
  computeMetrics,
  dateRangeFor,
  defaultAnalysisFilters,
  itemComparisons,
  fallingItems,
  risingItems,
  selectEvents,
  selectionRate,
  topRecommendedItems,
  unavailableHighDemandItems,
} from "../lib/analysis";

const last7 = () => {
  const filters = defaultAnalysisFilters();
  const range = dateRangeFor(filters);
  const compRange = comparisonRangeFor(range, filters.comparison)!;
  const current = selectEvents(analysisEvents, filters, range);
  const previous = selectEvents(analysisEvents, filters, compRange);
  return { filters, range, current, previous };
};

describe("date ranges", () => {
  it("computes preset ranges relative to today", () => {
    expect(
      dateRangeFor({ ...defaultAnalysisFilters(), preset: "today" }),
    ).toEqual({ start: TODAY_ISO, end: TODAY_ISO });
    expect(
      dateRangeFor({ ...defaultAnalysisFilters(), preset: "last-7" }),
    ).toEqual({ start: addDaysIso(TODAY_ISO, -6), end: TODAY_ISO });
    expect(
      dateRangeFor({ ...defaultAnalysisFilters(), preset: "last-30" }),
    ).toEqual({ start: addDaysIso(TODAY_ISO, -29), end: TODAY_ISO });
  });

  it("computes the previous-period comparison range", () => {
    const range = { start: addDaysIso(TODAY_ISO, -6), end: TODAY_ISO };
    expect(comparisonRangeFor(range, "previous-period")).toEqual({
      start: addDaysIso(TODAY_ISO, -13),
      end: addDaysIso(TODAY_ISO, -7),
    });
    expect(comparisonRangeFor(range, "none")).toBeNull();
  });
});

describe("metrics", () => {
  it("is a safe zero when there are no recommendations", () => {
    expect(selectionRate(5, 0)).toBe(0);
    expect(selectionRate(0, 0)).toBe(0);
    expect(computeMetrics([])).toMatchObject({
      recommendations: 0,
      selections: 0,
      selectionRate: 0,
    });
  });

  it("derives a positive selection rate between 0 and 1", () => {
    const { current } = last7();
    const m = computeMetrics(current);
    expect(m.recommendations).toBeGreaterThan(0);
    expect(m.selections).toBeGreaterThan(0);
    expect(m.selectionRate).toBeGreaterThan(0);
    expect(m.selectionRate).toBeLessThan(1);
  });
});

describe("rankings", () => {
  it("ranks Menu Item 01 (cat-01) as the top-demand item", () => {
    const { current } = last7();
    expect(topRecommendedItems(current, 1)[0].itemId).toBe("cat-01");
  });

  it("ranks Dining Hall A (loc-a) as the highest-demand location", () => {
    const { current } = last7();
    expect(byLocation(current)[0].key).toBe("loc-a");
  });
});

describe("trend detection", () => {
  it("flags cat-02 as rising and cat-03 as falling", () => {
    const { current, previous } = last7();
    const comparisons = itemComparisons(current, previous);
    expect(risingItems(comparisons).some((c) => c.itemId === "cat-02")).toBe(
      true,
    );
    expect(fallingItems(comparisons).some((c) => c.itemId === "cat-03")).toBe(
      true,
    );
  });
});

describe("signals", () => {
  it("derives a shortage-risk signal for the unavailable high-demand item", () => {
    const { current, previous } = last7();
    const signals = buildSignals(current, previous);
    expect(
      signals.some(
        (s) => s.type === "shortage-risk" && s.foodItemId === "cat-05",
      ),
    ).toBe(true);
  });

  it("derives an overproduction-risk signal for the low-selection item", () => {
    const { current, previous } = last7();
    const signals = buildSignals(current, previous);
    expect(
      signals.some(
        (s) => s.type === "overproduction-risk" && s.foodItemId === "cat-07",
      ),
    ).toBe(true);
  });

  it("can produce a stable-demand signal", () => {
    const { current, previous } = last7();
    const signals = buildSignals(current, previous);
    expect(signals.some((s) => s.type === "stable-demand")).toBe(true);
  });

  it("uses advisory interpretations, never exact commands", () => {
    const { current, previous } = last7();
    const signals = buildSignals(current, previous);
    for (const s of signals) {
      expect(s.interpretation).not.toMatch(/prepare exactly|immediately/i);
    }
  });
});

describe("unmet demand", () => {
  it("lists the unavailable high-demand item with a missed-selection estimate", () => {
    const { current } = last7();
    const unmet = unavailableHighDemandItems(current);
    const cat05 = unmet.find((u) => u.itemId === "cat-05");
    expect(cat05).toBeDefined();
    expect(cat05!.unavailableEvents).toBeGreaterThan(0);
    expect(cat05!.estimatedMissedSelections).toBeGreaterThanOrEqual(0);
  });
});
