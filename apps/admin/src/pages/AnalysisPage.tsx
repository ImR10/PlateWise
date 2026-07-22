import { useMemo, useState } from "react";

import {
  AnalysisFilters,
  COMPARISON_LABELS,
} from "../components/analysis/AnalysisFilters";
import { DataSourcePanel } from "../components/analysis/DataSourcePanel";
import { MetricCard } from "../components/analysis/MetricCard";
import { RankedBars } from "../components/analysis/RankedBars";
import { SelectionRateTable } from "../components/analysis/SelectionRateTable";
import { SignalCard } from "../components/analysis/SignalCard";
import { TimeBars } from "../components/analysis/TimeBars";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Icon } from "../components/ui/Icon";
import {
  ANALYSIS_LAST_UPDATED,
  analysisEvents,
  dataSources,
} from "../data/analysis";
import {
  SIGNAL_TYPE_LABEL,
  stationLabel,
  type SignalSeverity,
  type SignalType,
} from "../data/analysisTypes";
import { mealPeriodLabel } from "../data/menuTypes";
import { addDaysIso } from "../lib/dates";
import {
  buildSignals,
  byCategory,
  byLocation,
  byMealPeriod,
  byStation,
  comparisonRangeFor,
  computeMetrics,
  dateRangeFor,
  daysBetween,
  defaultAnalysisFilters,
  estimatedPrepared,
  estimatedUnused,
  fallingItems,
  itemComparisons,
  itemMetrics,
  risingItems,
  selectEvents,
  sumByType,
  topRecommendedItems,
  type AnalysisFilters as Filters,
} from "../lib/analysis";
import { useDiningLocations } from "../state/DiningLocationsProvider";
import { useFoodCatalog } from "../state/FoodCatalogProvider";

const LOW_VOLUME = 30;
const pct = (n: number) => `${Math.round(n * 100)}%`;
const changePct = (cur: number, prev: number): number | null =>
  prev > 0 ? (cur - prev) / prev : null;

export function AnalysisPage() {
  const { getFood } = useFoodCatalog();
  const { getLocationName } = useDiningLocations();
  const itemName = (id: string) => getFood(id)?.name ?? id;

  const [filters, setFilters] = useState<Filters>(defaultAnalysisFilters());
  const [signalType, setSignalType] = useState<SignalType | "all">("all");
  const [signalSeverity, setSignalSeverity] = useState<SignalSeverity | "all">(
    "all",
  );
  const [signalLocation, setSignalLocation] = useState<string>("all");

  const derived = useMemo(() => {
    const range = dateRangeFor(filters);
    const compRange = comparisonRangeFor(range, filters.comparison);
    const current = selectEvents(analysisEvents, filters, range);
    const previous = compRange
      ? selectEvents(analysisEvents, filters, compRange)
      : null;

    const metrics = computeMetrics(current);
    const prevMetrics = previous ? computeMetrics(previous) : null;
    const items = itemMetrics(current);
    const comparisons = itemComparisons(current, previous);
    const signals = buildSignals(current, previous);

    // Recommendations over time.
    const dayCount = daysBetween(range.start, range.end) + 1;
    const timePoints = Array.from({ length: dayCount }, (_, i) => {
      const date = addDaysIso(range.start, i);
      const value = sumByType(
        current.filter((e) => e.date === date),
        "recommendation-shown",
      );
      return { date, value };
    });

    return {
      range,
      compRange,
      current,
      metrics,
      prevMetrics,
      items,
      comparisons,
      signals,
      timePoints,
      locations: byLocation(current),
      meals: byMealPeriod(current),
      stations: byStation(current),
      categories: byCategory(current),
    };
  }, [filters]);

  const {
    metrics,
    prevMetrics,
    items,
    comparisons,
    signals,
    timePoints,
    locations,
    meals,
    stations,
    categories,
  } = derived;

  const hasComparison = filters.comparison !== "none" && prevMetrics !== null;
  const compLabel = COMPARISON_LABELS[filters.comparison].toLowerCase();

  const topItem = items[0];
  const topLocation = locations[0];
  const shortageItems = signals.filter((s) => s.type === "shortage-risk");
  const overproductionItems = signals.filter(
    (s) => s.type === "overproduction-risk",
  );

  const meaningful = items.filter((m) => m.recommendations >= LOW_VOLUME);
  const highestRate = [...meaningful].sort(
    (a, b) => b.selectionRate - a.selectionRate,
  )[0];
  const lowestRate = [...meaningful].sort(
    (a, b) => a.selectionRate - b.selectionRate,
  )[0];

  const wasteRows = items
    .filter((m) => m.recommendations >= LOW_VOLUME)
    .map((m) => ({
      id: m.itemId,
      prepared: estimatedPrepared(m.recommendations),
      selections: m.selections,
      unused: estimatedUnused(m.recommendations, m.selections),
    }))
    .sort((a, b) => b.unused - a.unused)
    .slice(0, 5);

  const unmet = derived.current
    .filter((e) => e.eventType === "item-unavailable")
    .reduce<Record<string, number>>((acc, e) => {
      acc[e.foodItemId] = (acc[e.foodItemId] ?? 0) + e.quantity;
      return acc;
    }, {});
  const unmetRows = items
    .filter((m) => unmet[m.itemId])
    .map((m) => ({
      id: m.itemId,
      recommendations: m.recommendations,
      unavailableEvents: unmet[m.itemId],
      missed: Math.round(unmet[m.itemId] * m.selectionRate),
    }));

  const signalTypesPresent = [...new Set(signals.map((s) => s.type))];
  const signalLocationsPresent = [
    ...new Set(signals.map((s) => s.locationId).filter(Boolean)),
  ] as string[];
  const filteredSignals = signals.filter(
    (s) =>
      (signalType === "all" || s.type === signalType) &&
      (signalSeverity === "all" || s.severity === signalSeverity) &&
      (signalLocation === "all" || s.locationId === signalLocation),
  );

  const isEmpty = metrics.recommendations === 0;

  const selectClass =
    "rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary";

  return (
    <div className="p-container-padding space-y-gutter max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div>
          <h2 className="font-h2 text-h2">Analysis</h2>
          <p className="text-body-sm text-secondary max-w-2xl">
            Operations analytics for dining administrators: recommendation
            demand, estimated selections, and planning signals. Last updated{" "}
            {ANALYSIS_LAST_UPDATED} (mock).
          </p>
        </div>
        <div className="flex flex-col items-start md:items-end gap-1">
          <Button
            variant="secondary"
            icon="download"
            disabled
            title="Available after analytics integration"
            aria-label="Export analytics (available after analytics integration)"
          >
            Export
          </Button>
          <span className="text-[11px] text-secondary">
            Available after analytics integration
          </span>
        </div>
      </div>

      {/* Mock-data notice */}
      <div
        role="note"
        className="admin-card p-gutter border-l-4 border-primary flex items-start gap-2"
      >
        <Icon name="info" className="text-primary shrink-0" />
        <p className="text-body-sm">
          <span className="font-bold">Analysis preview</span> — this page
          currently uses mock and estimated data. Real consumption, inventory,
          and waste metrics will require backend event tracking and
          dining-system integrations. This view is intended for product
          evaluation.
        </p>
      </div>

      <AnalysisFilters
        filters={filters}
        onChange={setFilters}
        onClear={() => setFilters(defaultAnalysisFilters())}
      />

      {isEmpty ? (
        <EmptyState
          icon="query_stats"
          title="No analytics match these filters"
          message="No mock events fall within the selected date range and filters. Try widening the date range or clearing filters."
          action={
            <Button
              variant="secondary"
              icon="filter_alt_off"
              onClick={() => setFilters(defaultAnalysisFilters())}
            >
              Clear filters
            </Button>
          }
        />
      ) : (
        <>
          {/* Summary metrics */}
          <section aria-label="Summary metrics">
            <h3 className="sr-only">Summary metrics</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-component-gap-md">
              <MetricCard
                title="Total recommendations"
                value={metrics.recommendations.toLocaleString()}
                caption="Mock recommendation events"
                description="How often items were recommended in this range."
                change={
                  hasComparison
                    ? {
                        pct: changePct(
                          metrics.recommendations,
                          prevMetrics!.recommendations,
                        ),
                        comparisonLabel: compLabel,
                      }
                    : undefined
                }
              />
              <MetricCard
                title="Estimated servings selected"
                value={metrics.selections.toLocaleString()}
                caption="Estimated from selection events"
                description="Estimated servings students selected — not confirmed consumption."
                estimated
                change={
                  hasComparison
                    ? {
                        pct: changePct(
                          metrics.selections,
                          prevMetrics!.selections,
                        ),
                        comparisonLabel: compLabel,
                      }
                    : undefined
                }
              />
              <MetricCard
                title="Estimated selection rate"
                value={pct(metrics.selectionRate)}
                caption="Estimated selections ÷ recommendations"
                description="Estimated share of recommendations that led to a selection."
                estimated
                change={
                  hasComparison
                    ? {
                        pct: changePct(
                          metrics.selectionRate,
                          prevMetrics!.selectionRate,
                        ),
                        comparisonLabel: compLabel,
                      }
                    : undefined
                }
              />
              <MetricCard
                title="Top-demand food item"
                value={topItem ? itemName(topItem.itemId) : "—"}
                caption={
                  topItem
                    ? `${topItem.recommendations.toLocaleString()} recommendations`
                    : undefined
                }
                description="Most recommended item in this range."
              />
              <MetricCard
                title="Highest-demand location"
                value={topLocation ? getLocationName(topLocation.key) : "—"}
                caption={
                  topLocation
                    ? `${topLocation.recommendations.toLocaleString()} recommendations`
                    : undefined
                }
                description="Dining location with the most recommendation demand."
              />
              <MetricCard
                title="Possible shortage risk"
                value={String(shortageItems.length)}
                caption="items"
                description="Items recommended while unavailable (possible unmet demand)."
                estimated
              />
              <MetricCard
                title="Possible overproduction risk"
                value={String(overproductionItems.length)}
                caption="items"
                description="Items with low estimated selection versus recommendation demand."
                estimated
              />
            </div>
          </section>

          {/* Recommendation demand */}
          <section
            aria-label="Recommendation demand"
            className="space-y-gutter"
          >
            <h3 className="font-h2 text-h2">Recommendation demand</h3>
            <TimeBars
              title="Recommendations over time"
              description="Mock recommendation events per day in the selected range."
              valueLabel="Recommendations"
              points={timePoints}
            />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-gutter">
              <RankedBars
                title="Most recommended items"
                description="Top items by mock recommendation volume."
                valueLabel="Recommendations"
                rows={topRecommendedItems(derived.current, 8).map((m) => ({
                  id: m.itemId,
                  label: itemName(m.itemId),
                  value: m.recommendations,
                  secondary: `${pct(m.selectionRate)} est. selection`,
                }))}
              />
              <RankedBars
                title="Recommendations by dining location"
                description="Mock recommendation volume per location."
                valueLabel="Recommendations"
                rows={locations.map((g) => ({
                  id: g.key,
                  label: getLocationName(g.key),
                  value: g.recommendations,
                }))}
              />
              <RankedBars
                title="Recommendations by meal period"
                description="Mock recommendation volume per meal period."
                valueLabel="Recommendations"
                rows={meals.map((g) => ({
                  id: g.key,
                  label: mealPeriodLabel(g.key as never),
                  value: g.recommendations,
                }))}
              />
              <RankedBars
                title="Recommendations by station"
                description="Mock recommendation volume per station."
                valueLabel="Recommendations"
                rows={stations.map((g) => ({
                  id: g.key,
                  label: stationLabel(g.key),
                  value: g.recommendations,
                }))}
              />
              <RankedBars
                title="Recommendations by category"
                description="Mock recommendation volume per food category."
                valueLabel="Recommendations"
                rows={categories.map((g) => ({
                  id: g.key,
                  label: g.key,
                  value: g.recommendations,
                }))}
              />
              <section
                className="admin-card p-gutter"
                aria-labelledby="rising-falling"
              >
                <h3 id="rising-falling" className="font-h3 text-h3">
                  Rising &amp; falling demand
                </h3>
                <p className="text-body-sm text-secondary mb-3">
                  Projected demand change versus the {compLabel}.
                </p>
                {!hasComparison ? (
                  <p className="text-body-sm text-secondary">
                    Select a comparison period to see rising and falling demand.
                  </p>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-body-md font-bold flex items-center gap-1 mb-1">
                        <Icon name="trending_up" className="text-[18px]" />
                        Rising
                      </h4>
                      <ul className="space-y-1 text-body-sm">
                        {risingItems(comparisons)
                          .slice(0, 5)
                          .map((c) => (
                            <li key={c.itemId} className="flex justify-between">
                              <span>{itemName(c.itemId)}</span>
                              <span className="font-bold">
                                +{Math.round((c.recsChangePct ?? 0) * 100)}%
                              </span>
                            </li>
                          ))}
                        {risingItems(comparisons).length === 0 ? (
                          <li className="text-secondary">None</li>
                        ) : null}
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-body-md font-bold flex items-center gap-1 mb-1">
                        <Icon name="trending_down" className="text-[18px]" />
                        Falling
                      </h4>
                      <ul className="space-y-1 text-body-sm">
                        {fallingItems(comparisons)
                          .slice(0, 5)
                          .map((c) => (
                            <li key={c.itemId} className="flex justify-between">
                              <span>{itemName(c.itemId)}</span>
                              <span className="font-bold">
                                {Math.round((c.recsChangePct ?? 0) * 100)}%
                              </span>
                            </li>
                          ))}
                        {fallingItems(comparisons).length === 0 ? (
                          <li className="text-secondary">None</li>
                        ) : null}
                      </ul>
                    </div>
                  </div>
                )}
              </section>
            </div>
          </section>

          {/* Estimated consumption */}
          <section
            aria-label="Estimated consumption"
            className="space-y-gutter"
          >
            <h3 className="font-h2 text-h2">Estimated consumption</h3>
            <p className="text-body-sm text-secondary max-w-2xl">
              These are <span className="font-bold">estimated selections</span>{" "}
              derived from mock recommendation and selection events — not
              confirmed consumption. PlateWise does not currently know what a
              student physically consumed.
            </p>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-gutter">
              <RankedBars
                title="Estimated servings by item"
                description="Estimated selections per item (mock)."
                valueLabel="Estimated servings"
                rows={[...items]
                  .sort((a, b) => b.selections - a.selections)
                  .slice(0, 8)
                  .map((m) => ({
                    id: m.itemId,
                    label: itemName(m.itemId),
                    value: m.selections,
                  }))}
              />
              <RankedBars
                title="Estimated servings by location"
                description="Estimated selections per location (mock)."
                valueLabel="Estimated servings"
                rows={[...locations]
                  .sort((a, b) => b.selections - a.selections)
                  .map((g) => ({
                    id: g.key,
                    label: getLocationName(g.key),
                    value: g.selections,
                  }))}
              />
              <RankedBars
                title="Estimated servings by meal period"
                description="Estimated selections per meal period (mock)."
                valueLabel="Estimated servings"
                rows={[...meals]
                  .sort((a, b) => b.selections - a.selections)
                  .map((g) => ({
                    id: g.key,
                    label: mealPeriodLabel(g.key as never),
                    value: g.selections,
                  }))}
              />
              <RankedBars
                title="Estimated servings by category"
                description="Estimated selections per category (mock)."
                valueLabel="Estimated servings"
                rows={[...categories]
                  .sort((a, b) => b.selections - a.selections)
                  .map((g) => ({
                    id: g.key,
                    label: g.key,
                    value: g.selections,
                  }))}
              />
            </div>
          </section>

          {/* Selection-rate analysis */}
          <section
            aria-labelledby="selection-rate"
            className="admin-card p-gutter space-y-3"
          >
            <div>
              <h3 id="selection-rate" className="font-h3 text-h3">
                Recommendation-to-selection analysis
              </h3>
              <p className="text-body-sm text-secondary">
                Estimated selection rate = estimated selections ÷
                recommendations. Low-volume items are flagged; items with zero
                recommendations show no rate.
              </p>
            </div>
            {highestRate || lowestRate ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-body-sm">
                {highestRate ? (
                  <p className="admin-card p-3">
                    Highest estimated selection rate:{" "}
                    <span className="font-bold">
                      {itemName(highestRate.itemId)}
                    </span>{" "}
                    ({pct(highestRate.selectionRate)})
                  </p>
                ) : null}
                {lowestRate ? (
                  <p className="admin-card p-3">
                    High recommendations, low estimated selection:{" "}
                    <span className="font-bold">
                      {itemName(lowestRate.itemId)}
                    </span>{" "}
                    ({pct(lowestRate.selectionRate)})
                  </p>
                ) : null}
              </div>
            ) : null}
            <SelectionRateTable
              rows={comparisons.map((c) => ({
                id: c.itemId,
                itemName: itemName(c.itemId),
                recommendations: c.current.recommendations,
                selections: c.current.selections,
                rate: c.current.selectionRate,
                changePct: c.recsChangePct,
                lowVolume: c.current.recommendations < LOW_VOLUME,
              }))}
            />
          </section>

          {/* Inventory-planning signals */}
          <section
            aria-label="Inventory-planning signals"
            className="space-y-3"
          >
            <div>
              <h3 className="font-h2 text-h2">Inventory-planning signals</h3>
              <p className="text-body-sm text-secondary max-w-2xl">
                Advisory planning signals derived from mock demand. These are
                suggestions for review, not automatic instructions.
              </p>
            </div>
            <div className="flex flex-wrap gap-component-gap-md">
              <label className="text-body-sm">
                <span className="sr-only">Filter signals by type</span>
                <select
                  className={selectClass}
                  value={signalType}
                  aria-label="Filter signals by type"
                  onChange={(e) =>
                    setSignalType(e.target.value as SignalType | "all")
                  }
                >
                  <option value="all">All signal types</option>
                  {signalTypesPresent.map((t) => (
                    <option key={t} value={t}>
                      {SIGNAL_TYPE_LABEL[t]}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-body-sm">
                <span className="sr-only">Filter signals by severity</span>
                <select
                  className={selectClass}
                  value={signalSeverity}
                  aria-label="Filter signals by severity"
                  onChange={(e) =>
                    setSignalSeverity(e.target.value as SignalSeverity | "all")
                  }
                >
                  <option value="all">All severities</option>
                  <option value="risk">Possible risk</option>
                  <option value="watch">Watch</option>
                  <option value="info">Info</option>
                </select>
              </label>
              <label className="text-body-sm">
                <span className="sr-only">Filter signals by location</span>
                <select
                  className={selectClass}
                  value={signalLocation}
                  aria-label="Filter signals by location"
                  onChange={(e) => setSignalLocation(e.target.value)}
                >
                  <option value="all">All locations</option>
                  {signalLocationsPresent.map((l) => (
                    <option key={l} value={l}>
                      {getLocationName(l)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {filteredSignals.length === 0 ? (
              <p className="admin-card p-gutter text-body-sm text-secondary text-center py-8">
                No signals match the current signal filters.
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-gutter">
                {filteredSignals.map((s) => (
                  <SignalCard
                    key={s.id}
                    signal={s}
                    itemName={itemName(s.foodItemId)}
                    locationName={
                      s.locationId ? getLocationName(s.locationId) : undefined
                    }
                  />
                ))}
              </div>
            )}
          </section>

          {/* Availability & unmet demand */}
          <section
            aria-labelledby="unmet-demand"
            className="admin-card p-gutter space-y-3"
          >
            <div>
              <h3 id="unmet-demand" className="font-h3 text-h3">
                Availability &amp; unmet demand
              </h3>
              <p className="text-body-sm text-secondary">
                Items recommended while unavailable, with an estimate of missed
                selections. Can support possible shortage-risk signals.
              </p>
            </div>
            {unmetRows.length === 0 ? (
              <p className="text-body-sm text-secondary py-2">
                No items were recommended while unavailable in this range.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-body-sm min-w-[520px]">
                  <caption className="sr-only">
                    Items recommended while unavailable and estimated missed
                    selections.
                  </caption>
                  <thead>
                    <tr className="text-left text-label-md text-secondary uppercase border-b border-outline-variant">
                      <th scope="col" className="py-2 pr-3 font-semibold">
                        Item
                      </th>
                      <th scope="col" className="py-2 pr-3 font-semibold">
                        Recommendations
                      </th>
                      <th scope="col" className="py-2 pr-3 font-semibold">
                        Unavailable events
                      </th>
                      <th scope="col" className="py-2 font-semibold">
                        Estimated missed selections
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {unmetRows.map((r) => (
                      <tr
                        key={r.id}
                        className="border-b border-outline-variant"
                      >
                        <th scope="row" className="py-2 pr-3 font-bold">
                          {itemName(r.id)}
                        </th>
                        <td className="py-2 pr-3 tabular-nums">
                          {r.recommendations.toLocaleString()}
                        </td>
                        <td className="py-2 pr-3 tabular-nums">
                          {r.unavailableEvents}
                        </td>
                        <td className="py-2 tabular-nums">{r.missed}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Waste & overproduction estimates */}
          <section
            aria-labelledby="waste"
            className="admin-card p-gutter space-y-3"
          >
            <div>
              <h3 id="waste" className="font-h3 text-h3">
                Waste &amp; overproduction estimates
              </h3>
              <p className="text-body-sm text-secondary max-w-2xl">
                <span className="font-bold">
                  Requires inventory integration.
                </span>{" "}
                These are waste-risk estimates from mock demand only — not a
                measurement of actual waste. Real waste analytics would require
                servings prepared, servings taken, leftovers, discarded food,
                point-of-sale counts, and kitchen inventory records.
              </p>
            </div>
            {wasteRows.length === 0 ? (
              <p className="text-body-sm text-secondary py-2">
                No overproduction-risk estimates for the current filters.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-body-sm min-w-[520px]">
                  <caption className="sr-only">
                    Estimated prepared servings, estimated selections, and
                    estimated unused servings per item.
                  </caption>
                  <thead>
                    <tr className="text-left text-label-md text-secondary uppercase border-b border-outline-variant">
                      <th scope="col" className="py-2 pr-3 font-semibold">
                        Item
                      </th>
                      <th scope="col" className="py-2 pr-3 font-semibold">
                        Est. prepared
                      </th>
                      <th scope="col" className="py-2 pr-3 font-semibold">
                        Est. selections
                      </th>
                      <th scope="col" className="py-2 font-semibold">
                        Estimated unused servings
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {wasteRows.map((r) => (
                      <tr
                        key={r.id}
                        className="border-b border-outline-variant"
                      >
                        <th scope="row" className="py-2 pr-3 font-bold">
                          {itemName(r.id)}
                        </th>
                        <td className="py-2 pr-3 tabular-nums">
                          {r.prepared.toLocaleString()}
                        </td>
                        <td className="py-2 pr-3 tabular-nums">
                          {r.selections.toLocaleString()}
                        </td>
                        <td className="py-2 tabular-nums">
                          {r.unused.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Data sources & quality */}
          <DataSourcePanel rows={dataSources} />
        </>
      )}
    </div>
  );
}
