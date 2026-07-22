import { ANALYSIS_STATIONS } from "../../data/analysisTypes";
import { FOOD_CATEGORIES, MEAL_PERIODS } from "../../data/menuTypes";
import type { AnalysisFilters as Filters } from "../../lib/analysis";
import { useDiningLocations } from "../../state/DiningLocationsProvider";
import { Button } from "../ui/Button";

const selectClass =
  "w-full rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary";
const labelClass = "block text-label-md text-secondary uppercase mb-1";

export const PRESET_LABELS: Record<Filters["preset"], string> = {
  today: "Today",
  "last-7": "Last 7 days",
  "last-30": "Last 30 days",
  custom: "Custom",
};

export const COMPARISON_LABELS: Record<Filters["comparison"], string> = {
  "previous-period": "Previous period",
  "previous-week": "Previous week",
  none: "No comparison",
};

export const analysisFiltersActive = (f: Filters): boolean =>
  f.preset !== "last-7" ||
  f.locationId !== "all" ||
  f.mealPeriod !== "all" ||
  f.stationId !== "all" ||
  f.category !== "all" ||
  f.comparison !== "previous-period";

interface AnalysisFiltersProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
  onClear: () => void;
}

export function AnalysisFilters({
  filters,
  onChange,
  onClear,
}: AnalysisFiltersProps) {
  const { locations } = useDiningLocations();
  const set = (patch: Partial<Filters>) => onChange({ ...filters, ...patch });

  return (
    <section
      className="admin-card p-gutter space-y-component-gap-md"
      aria-label="Analysis filters"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-component-gap-md">
        <div>
          <label htmlFor="an-range" className={labelClass}>
            Date range
          </label>
          <select
            id="an-range"
            className={selectClass}
            value={filters.preset}
            onChange={(e) =>
              set({ preset: e.target.value as Filters["preset"] })
            }
          >
            {(Object.keys(PRESET_LABELS) as Filters["preset"][]).map((p) => (
              <option key={p} value={p}>
                {PRESET_LABELS[p]}
              </option>
            ))}
          </select>
        </div>

        {filters.preset === "custom" ? (
          <>
            <div>
              <label htmlFor="an-start" className={labelClass}>
                Start date
              </label>
              <input
                id="an-start"
                type="date"
                className={selectClass}
                value={filters.customStart}
                onChange={(e) => set({ customStart: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="an-end" className={labelClass}>
                End date
              </label>
              <input
                id="an-end"
                type="date"
                className={selectClass}
                value={filters.customEnd}
                onChange={(e) => set({ customEnd: e.target.value })}
              />
            </div>
          </>
        ) : null}

        <div>
          <label htmlFor="an-comparison" className={labelClass}>
            Comparison period
          </label>
          <select
            id="an-comparison"
            className={selectClass}
            value={filters.comparison}
            onChange={(e) =>
              set({ comparison: e.target.value as Filters["comparison"] })
            }
          >
            {(Object.keys(COMPARISON_LABELS) as Filters["comparison"][]).map(
              (c) => (
                <option key={c} value={c}>
                  {COMPARISON_LABELS[c]}
                </option>
              ),
            )}
          </select>
        </div>

        <div>
          <label htmlFor="an-location" className={labelClass}>
            Dining location
          </label>
          <select
            id="an-location"
            className={selectClass}
            value={filters.locationId}
            onChange={(e) => set({ locationId: e.target.value })}
          >
            <option value="all">All Locations</option>
            {locations.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="an-meal" className={labelClass}>
            Meal period
          </label>
          <select
            id="an-meal"
            className={selectClass}
            value={filters.mealPeriod}
            onChange={(e) =>
              set({ mealPeriod: e.target.value as Filters["mealPeriod"] })
            }
          >
            <option value="all">All Meals</option>
            {MEAL_PERIODS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="an-station" className={labelClass}>
            Station
          </label>
          <select
            id="an-station"
            className={selectClass}
            value={filters.stationId}
            onChange={(e) => set({ stationId: e.target.value })}
          >
            <option value="all">All Stations</option>
            {ANALYSIS_STATIONS.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="an-category" className={labelClass}>
            Food category
          </label>
          <select
            id="an-category"
            className={selectClass}
            value={filters.category}
            onChange={(e) =>
              set({ category: e.target.value as Filters["category"] })
            }
          >
            <option value="all">All Categories</option>
            {FOOD_CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      {analysisFiltersActive(filters) ? (
        <div className="flex justify-end">
          <Button variant="ghost" icon="filter_alt_off" onClick={onClear}>
            Clear filters
          </Button>
        </div>
      ) : null}
    </section>
  );
}
