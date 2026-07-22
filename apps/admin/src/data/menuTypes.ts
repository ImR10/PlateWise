/**
 * Domain types and label maps for the frontend-only Menus feature.
 *
 * Everything here is generic mock-data scaffolding. There is no backend,
 * persistence, or API integration behind these types — see the Menus provider
 * (`src/state/MenusProvider.tsx`) for the in-memory session state that uses
 * them. All names are generic placeholders (no real institutions, dining
 * locations, dishes, or people).
 */
import type { StatusTone } from "./types";

export type MenuStatus =
  | "draft"
  | "published"
  | "needs-attention"
  | "scheduled";

export type MealPeriod = "breakfast" | "lunch" | "dinner" | "late-night";

export type AvailabilityStatus = "available" | "limited" | "unavailable";

export type FoodCategory =
  | "Category A"
  | "Category B"
  | "Category C"
  | "Category D";

export type DietaryTag = "Vegetarian" | "Vegan" | "Gluten-Free" | "Halal";

export type Allergen =
  | "Milk"
  | "Eggs"
  | "Fish"
  | "Shellfish"
  | "Tree Nuts"
  | "Peanuts"
  | "Wheat"
  | "Soy"
  | "Sesame";

/** Who last touched a menu. Only generic placeholders / the System actor. */
export type ActivityActor = "John Doe" | "Jane Doe" | "System";

export interface DiningLocation {
  id: string;
  name: string;
}

/** An item in the reusable food catalog used by the "Add Food Item" flow. */
export interface FoodCatalogItem {
  id: string;
  name: string;
  category: FoodCategory;
  dietaryTags: DietaryTag[];
  allergens: Allergen[];
  description?: string;
}

/** A food item placed on a specific menu station. */
export interface MenuItem {
  id: string;
  name: string;
  category: FoodCategory;
  dietaryTags: DietaryTag[];
  allergens: Allergen[];
  availability: AvailabilityStatus;
  /** Optional student-facing note (shown in preview). */
  studentNote?: string;
  /** Provenance link back to the catalog item, when added from the catalog. */
  catalogId?: string;
}

export interface MenuStation {
  id: string;
  name: string;
  items: MenuItem[];
}

export interface Menu {
  id: string;
  locationId: string;
  date: string; // ISO calendar date, YYYY-MM-DD
  mealPeriod: MealPeriod;
  status: MenuStatus;
  /** Internal working title for staff. */
  title: string;
  /** Internal notes — never shown to students / in preview. */
  internalNotes?: string;
  stations: MenuStation[];
  /** Human-readable "last updated" label (mock, session-relative). */
  updatedAt: string;
  updatedBy: ActivityActor;
}

/** A single reason a menu cannot be published yet. */
export interface MenuValidationIssue {
  id: string;
  message: string;
  stationId?: string;
  itemId?: string;
  field?: string;
}

/* --- Label maps and option lists (single source of truth for UI copy) --- */

export const MEAL_PERIODS: { value: MealPeriod; label: string }[] = [
  { value: "breakfast", label: "Breakfast" },
  { value: "lunch", label: "Lunch" },
  { value: "dinner", label: "Dinner" },
  { value: "late-night", label: "Late Night" },
];

export const MENU_STATUSES: { value: MenuStatus; label: string }[] = [
  { value: "draft", label: "Draft" },
  { value: "published", label: "Published" },
  { value: "needs-attention", label: "Needs Attention" },
  { value: "scheduled", label: "Scheduled" },
];

export const AVAILABILITY_OPTIONS: {
  value: AvailabilityStatus;
  label: string;
}[] = [
  { value: "available", label: "Available" },
  { value: "limited", label: "Limited" },
  { value: "unavailable", label: "Unavailable" },
];

export const FOOD_CATEGORIES: FoodCategory[] = [
  "Category A",
  "Category B",
  "Category C",
  "Category D",
];

export const DIETARY_TAGS: DietaryTag[] = [
  "Vegetarian",
  "Vegan",
  "Gluten-Free",
  "Halal",
];

export const ALLERGENS: Allergen[] = [
  "Milk",
  "Eggs",
  "Fish",
  "Shellfish",
  "Tree Nuts",
  "Peanuts",
  "Wheat",
  "Soy",
  "Sesame",
];

export const mealPeriodLabel = (value: MealPeriod): string =>
  MEAL_PERIODS.find((m) => m.value === value)?.label ?? value;

export const menuStatusLabel = (value: MenuStatus): string =>
  MENU_STATUSES.find((s) => s.value === value)?.label ?? value;

export const availabilityLabel = (value: AvailabilityStatus): string =>
  AVAILABILITY_OPTIONS.find((a) => a.value === value)?.label ?? value;

/** Map a menu status to the shared StatusBadge tone. */
export const menuStatusTone: Record<MenuStatus, StatusTone> = {
  draft: "neutral",
  published: "success",
  "needs-attention": "warning",
  scheduled: "info",
};

/** Map an availability value to a StatusBadge tone. */
export const availabilityTone: Record<AvailabilityStatus, StatusTone> = {
  available: "success",
  limited: "warning",
  unavailable: "danger",
};
