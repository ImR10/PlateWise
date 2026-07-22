/**
 * Managed food-catalog domain types for the frontend-only Food Catalog feature.
 * This record is the superset the Menus "Add Food Item" flow also consumes.
 * Generic mock data only, held in memory for the session — no backend.
 */
import type { StatusTone } from "./types";
import type {
  ActivityActor,
  Allergen,
  AvailabilityStatus,
  DietaryTag,
  FoodCategory,
} from "./menuTypes";

export type FoodStatus = "draft" | "active" | "archived";

export interface FoodCatalogItem {
  id: string;
  name: string;
  category: FoodCategory;
  dietaryTags: DietaryTag[];
  allergens: Allergen[];
  /** Short student-facing description. */
  description?: string;
  /** Longer optional student-facing description. */
  longDescription?: string;
  status: FoodStatus;
  studentVisible: boolean;
  /** Internal notes — never shown to students / in preview. */
  internalNotes?: string;
  defaultAvailability: AvailabilityStatus;
  /** Lightweight admin-catalog serving metadata (not a nutrition system). */
  servingLabel?: string;
  calories?: string;
  portion?: string;
  updatedAt: string;
  updatedBy: ActivityActor;
}

export const FOOD_STATUSES: { value: FoodStatus; label: string }[] = [
  { value: "draft", label: "Draft" },
  { value: "active", label: "Active" },
  { value: "archived", label: "Archived" },
];

export const foodStatusLabel = (value: FoodStatus): string =>
  FOOD_STATUSES.find((s) => s.value === value)?.label ?? value;

export const foodStatusTone: Record<FoodStatus, StatusTone> = {
  draft: "neutral",
  active: "success",
  archived: "danger",
};
