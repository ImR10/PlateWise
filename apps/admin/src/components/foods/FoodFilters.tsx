import { FOOD_STATUSES, type FoodStatus } from "../../data/foodTypes";
import {
  ALLERGENS,
  DIETARY_TAGS,
  FOOD_CATEGORIES,
  type Allergen,
  type DietaryTag,
  type FoodCategory,
} from "../../data/menuTypes";
import { Button } from "../ui/Button";

export interface FoodFilterState {
  search: string;
  category: FoodCategory | "all";
  dietary: DietaryTag | "all";
  allergen: Allergen | "all";
  status: FoodStatus | "all";
  showArchived: boolean;
}

export const emptyFoodFilters: FoodFilterState = {
  search: "",
  category: "all",
  dietary: "all",
  allergen: "all",
  status: "all",
  showArchived: false,
};

export const foodFiltersActive = (f: FoodFilterState): boolean =>
  f.search.trim() !== "" ||
  f.category !== "all" ||
  f.dietary !== "all" ||
  f.allergen !== "all" ||
  f.status !== "all" ||
  f.showArchived;

const selectClass =
  "w-full rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary";
const labelClass = "block text-label-md text-secondary uppercase mb-1";

interface FoodFiltersProps {
  filters: FoodFilterState;
  onChange: (filters: FoodFilterState) => void;
  onClear: () => void;
}

export function FoodFilters({ filters, onChange, onClear }: FoodFiltersProps) {
  return (
    <div className="admin-card p-gutter space-y-component-gap-md">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-component-gap-md">
        <div className="sm:col-span-2 lg:col-span-1">
          <label htmlFor="food-search" className={labelClass}>
            Search
          </label>
          <input
            id="food-search"
            type="search"
            className={selectClass}
            placeholder="Search food items"
            value={filters.search}
            onChange={(e) => onChange({ ...filters, search: e.target.value })}
          />
        </div>
        <div>
          <label htmlFor="food-category" className={labelClass}>
            Category
          </label>
          <select
            id="food-category"
            className={selectClass}
            value={filters.category}
            onChange={(e) =>
              onChange({
                ...filters,
                category: e.target.value as FoodFilterState["category"],
              })
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
        <div>
          <label htmlFor="food-dietary" className={labelClass}>
            Dietary tag
          </label>
          <select
            id="food-dietary"
            className={selectClass}
            value={filters.dietary}
            onChange={(e) =>
              onChange({
                ...filters,
                dietary: e.target.value as FoodFilterState["dietary"],
              })
            }
          >
            <option value="all">All Dietary Tags</option>
            {DIETARY_TAGS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="food-allergen" className={labelClass}>
            Allergen
          </label>
          <select
            id="food-allergen"
            className={selectClass}
            value={filters.allergen}
            onChange={(e) =>
              onChange({
                ...filters,
                allergen: e.target.value as FoodFilterState["allergen"],
              })
            }
          >
            <option value="all">All Allergens</option>
            {ALLERGENS.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="food-status" className={labelClass}>
            Status
          </label>
          <select
            id="food-status"
            className={selectClass}
            value={filters.status}
            onChange={(e) =>
              onChange({
                ...filters,
                status: e.target.value as FoodFilterState["status"],
              })
            }
          >
            <option value="all">All Statuses</option>
            {FOOD_STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
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
          Show archived items
        </label>
        {foodFiltersActive(filters) ? (
          <Button variant="ghost" icon="filter_alt_off" onClick={onClear}>
            Clear filters
          </Button>
        ) : null}
      </div>
    </div>
  );
}
