/**
 * Generic reusable food-catalog mock data for the "Add Food Item" flow.
 * Item names are placeholders only (no real dishes, brands, or recipes).
 */
import type { FoodCatalogItem } from "./menuTypes";

export const foodCatalog: FoodCatalogItem[] = [
  {
    id: "cat-01",
    name: "Menu Item 01",
    category: "Category A",
    dietaryTags: ["Vegetarian"],
    allergens: ["Milk", "Wheat"],
    description: "Generic placeholder catalog item.",
  },
  {
    id: "cat-02",
    name: "Menu Item 02",
    category: "Category A",
    dietaryTags: ["Vegan", "Gluten-Free"],
    allergens: ["Soy"],
    description: "Generic placeholder catalog item.",
  },
  {
    id: "cat-03",
    name: "Menu Item 03",
    category: "Category B",
    dietaryTags: ["Halal"],
    allergens: ["Eggs"],
    description: "Generic placeholder catalog item.",
  },
  {
    id: "cat-04",
    name: "Menu Item 04",
    category: "Category B",
    dietaryTags: ["Vegetarian", "Gluten-Free"],
    allergens: ["Tree Nuts"],
    description: "Generic placeholder catalog item.",
  },
  {
    id: "cat-05",
    name: "Menu Item 05",
    category: "Category C",
    dietaryTags: [],
    allergens: ["Fish"],
    description: "Generic placeholder catalog item.",
  },
  {
    id: "cat-06",
    name: "Menu Item 06",
    category: "Category C",
    dietaryTags: ["Vegan"],
    allergens: ["Peanuts", "Sesame"],
    description: "Generic placeholder catalog item.",
  },
  {
    id: "cat-07",
    name: "Menu Item 07",
    category: "Category D",
    dietaryTags: ["Vegetarian"],
    allergens: ["Milk"],
    description: "Generic placeholder catalog item.",
  },
  {
    id: "cat-08",
    name: "Menu Item 08",
    category: "Category D",
    dietaryTags: ["Halal", "Gluten-Free"],
    allergens: ["Shellfish"],
    description: "Generic placeholder catalog item.",
  },
  {
    id: "cat-09",
    name: "Menu Item 09",
    category: "Category A",
    dietaryTags: ["Vegan"],
    allergens: [],
    description: "Generic placeholder catalog item.",
  },
  {
    id: "cat-10",
    name: "Menu Item 10",
    category: "Category B",
    dietaryTags: ["Vegetarian"],
    allergens: ["Wheat", "Soy"],
    description: "Generic placeholder catalog item.",
  },
  {
    id: "cat-11",
    name: "Menu Item 11",
    category: "Category C",
    dietaryTags: ["Gluten-Free"],
    allergens: ["Eggs", "Milk"],
    description: "Generic placeholder catalog item.",
  },
  {
    id: "cat-12",
    name: "Menu Item 12",
    category: "Category D",
    dietaryTags: ["Halal"],
    allergens: ["Tree Nuts", "Peanuts"],
    description: "Generic placeholder catalog item.",
  },
];
