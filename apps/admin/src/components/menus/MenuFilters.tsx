import {
  MEAL_PERIODS,
  MENU_STATUSES,
  type MealPeriod,
  type MenuStatus,
} from "../../data/menuTypes";
import { useDiningLocations } from "../../state/DiningLocationsProvider";
import { Button } from "../ui/Button";

export interface MenuFilterState {
  locationId: string | "all";
  mealPeriod: MealPeriod | "all";
  status: MenuStatus | "all";
}

export const emptyFilters: MenuFilterState = {
  locationId: "all",
  mealPeriod: "all",
  status: "all",
};

export const filtersActive = (filters: MenuFilterState): boolean =>
  filters.locationId !== "all" ||
  filters.mealPeriod !== "all" ||
  filters.status !== "all";

interface MenuFiltersProps {
  filters: MenuFilterState;
  onChange: (filters: MenuFilterState) => void;
  onClear: () => void;
}

const selectClass =
  "w-full rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary";

export function MenuFilters({ filters, onChange, onClear }: MenuFiltersProps) {
  const { locations } = useDiningLocations();
  const active = filtersActive(filters);

  return (
    <div className="admin-card p-gutter">
      <div className="flex flex-wrap items-end gap-component-gap-md">
        <div className="flex-1 min-w-[160px]">
          <label
            htmlFor="filter-location"
            className="block text-label-md text-secondary uppercase mb-1"
          >
            Dining location
          </label>
          <select
            id="filter-location"
            className={selectClass}
            value={filters.locationId}
            onChange={(e) =>
              onChange({ ...filters, locationId: e.target.value })
            }
          >
            <option value="all">All Locations</option>
            {locations.map((loc) => (
              <option key={loc.id} value={loc.id}>
                {loc.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1 min-w-[160px]">
          <label
            htmlFor="filter-meal"
            className="block text-label-md text-secondary uppercase mb-1"
          >
            Meal period
          </label>
          <select
            id="filter-meal"
            className={selectClass}
            value={filters.mealPeriod}
            onChange={(e) =>
              onChange({
                ...filters,
                mealPeriod: e.target.value as MenuFilterState["mealPeriod"],
              })
            }
          >
            <option value="all">All Meals</option>
            {MEAL_PERIODS.map((meal) => (
              <option key={meal.value} value={meal.value}>
                {meal.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1 min-w-[160px]">
          <label
            htmlFor="filter-status"
            className="block text-label-md text-secondary uppercase mb-1"
          >
            Status
          </label>
          <select
            id="filter-status"
            className={selectClass}
            value={filters.status}
            onChange={(e) =>
              onChange({
                ...filters,
                status: e.target.value as MenuFilterState["status"],
              })
            }
          >
            <option value="all">All Statuses</option>
            {MENU_STATUSES.map((status) => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>
        </div>

        {active ? (
          <Button variant="ghost" icon="filter_alt_off" onClick={onClear}>
            Clear filters
          </Button>
        ) : null}
      </div>
    </div>
  );
}
