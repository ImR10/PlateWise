/**
 * Pure, immutable transforms over the food-catalog domain.
 */
import type { FoodCatalogItem } from "../data/foodTypes";
import type { Allergen, DietaryTag } from "../data/menuTypes";
import { createId } from "../lib/ids";

export const touchFood = (food: FoodCatalogItem): FoodCatalogItem => ({
  ...food,
  updatedAt: "Just now",
  updatedBy: "John Doe",
});

export const buildFood = (): FoodCatalogItem => ({
  id: createId("cat"),
  name: "",
  category: "Category A",
  dietaryTags: [],
  allergens: [],
  description: "",
  status: "draft",
  studentVisible: false,
  defaultAvailability: "available",
  updatedAt: "Just now",
  updatedBy: "John Doe",
});

export const cloneFood = (food: FoodCatalogItem): FoodCatalogItem => ({
  ...food,
  id: createId("cat"),
  name: `${food.name} (copy)`,
  status: "draft",
  dietaryTags: [...food.dietaryTags],
  allergens: [...food.allergens],
  updatedAt: "Just now",
  updatedBy: "John Doe",
});

export const toggleDietaryTag = (
  food: FoodCatalogItem,
  tag: DietaryTag,
): FoodCatalogItem => ({
  ...food,
  dietaryTags: food.dietaryTags.includes(tag)
    ? food.dietaryTags.filter((t) => t !== tag)
    : [...food.dietaryTags, tag],
});

export const toggleAllergen = (
  food: FoodCatalogItem,
  allergen: Allergen,
): FoodCatalogItem => ({
  ...food,
  allergens: food.allergens.includes(allergen)
    ? food.allergens.filter((a) => a !== allergen)
    : [...food.allergens, allergen],
});

export const clearAllergens = (food: FoodCatalogItem): FoodCatalogItem => ({
  ...food,
  allergens: [],
});
