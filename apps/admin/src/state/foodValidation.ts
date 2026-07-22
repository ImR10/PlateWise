/**
 * Validation for activating/publishing a food item. Pure function — returns the
 * reasons the item cannot be made active yet.
 */
import type { FoodCatalogItem } from "../data/foodTypes";
import { FOOD_CATEGORIES } from "../data/menuTypes";
import type { ValidationIssue } from "./locationValidation";

export type { ValidationIssue };

export function validateFoodForActivation(
  food: FoodCatalogItem,
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  if (!food.name.trim()) {
    issues.push({ id: "name", message: "Enter a food-item name." });
  }
  if (!FOOD_CATEGORIES.includes(food.category)) {
    issues.push({ id: "category", message: "Select a category." });
  }

  return issues;
}
