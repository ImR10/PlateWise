import {
  LOCATION_STATUSES,
  type LocationStatus,
} from "../../data/locationTypes";
import { MEAL_PERIODS, type MealPeriod } from "../../data/menuTypes";
import { Button } from "../ui/Button";

export interface LocationFilterState {
  search: string;
  status: LocationStatus | "all";
  mealPeriod: MealPeriod | "all";
  showArchived: boolean;
}

export const emptyLocationFilters: LocationFilterState = {
  search: "",
  status: "all",
  mealPeriod: "all",
  showArchived: false,
};

export const locationFiltersActive = (f: LocationFilterState): boolean =>
  f.search.trim() !== "" ||
  f.status !== "all" ||
  f.mealPeriod !== "all" ||
  f.showArchived;

const selectClass =
  "w-full rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary";
const labelClass = "block text-label-md text-secondary uppercase mb-1";

interface LocationFiltersProps {
  filters: LocationFilterState;
  onChange: (filters: LocationFilterState) => void;
  onClear: () => void;
}

export function LocationFilters({
  filters,
  onChange,
  onClear,
}: LocationFiltersProps) {
  return (
    <div className="admin-card p-gutter space-y-component-gap-md">
      <div className="flex flex-wrap items-end gap-component-gap-md">
        <div className="flex-1 min-w-[200px]">
          <label htmlFor="location-search" className={labelClass}>
            Search
          </label>
          <input
            id="location-search"
            type="search"
            className={selectClass}
            placeholder="Search locations"
            value={filters.search}
            onChange={(e) => onChange({ ...filters, search: e.target.value })}
          />
        </div>
        <div className="flex-1 min-w-[160px]">
          <label htmlFor="location-status" className={labelClass}>
            Status
          </label>
          <select
            id="location-status"
            className={selectClass}
            value={filters.status}
            onChange={(e) =>
              onChange({
                ...filters,
                status: e.target.value as LocationFilterState["status"],
              })
            }
          >
            <option value="all">All Statuses</option>
            {LOCATION_STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1 min-w-[160px]">
          <label htmlFor="location-meal" className={labelClass}>
            Meal period
          </label>
          <select
            id="location-meal"
            className={selectClass}
            value={filters.mealPeriod}
            onChange={(e) =>
              onChange({
                ...filters,
                mealPeriod: e.target.value as LocationFilterState["mealPeriod"],
              })
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
      </div>
      <div className="flex flex-wrap items-center justify-between gap-component-gap-md">
        <label className="flex items-center gap-2 text-body-sm">
          <input
            type="checkbox"
            checked={filters.showArchived}
            onChange={(e) =>
              onChange({ ...filters, showArchived: e.target.checked })
            }
          />
          Show archived locations
        </label>
        {locationFiltersActive(filters) ? (
          <Button variant="ghost" icon="filter_alt_off" onClick={onClear}>
            Clear filters
          </Button>
        ) : null}
      </div>
    </div>
  );
}
