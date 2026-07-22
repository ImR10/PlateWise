/**
 * Initial in-memory mock menus for the Menus feature.
 *
 * This is the seed state loaded into the Menus provider at session start.
 * Everything is generic placeholder data (Dining Hall A–E, Menu Item NN,
 * Station A–E, John/Jane Doe/System). There is no backend: edits live only in
 * React state for the session and are reset on refresh.
 */
import { TODAY_ISO, addDaysIso } from "../lib/dates";
import type { Menu } from "./menuTypes";

const TOMORROW_ISO = addDaysIso(TODAY_ISO, 1);

export const initialMenus: Menu[] = [
  {
    id: "menu-a-breakfast",
    locationId: "loc-a",
    date: TODAY_ISO,
    mealPeriod: "breakfast",
    status: "published",
    title: "Morning service",
    internalNotes: "Internal setup note — not shown to students.",
    updatedAt: "2h ago",
    updatedBy: "Jane Doe",
    stations: [
      {
        id: "st-a1",
        name: "Station A",
        items: [
          {
            id: "it-a1-1",
            name: "Menu Item 01",
            category: "Category A",
            dietaryTags: ["Vegetarian"],
            allergens: ["Milk", "Wheat"],
            availability: "available",
          },
          {
            id: "it-a1-2",
            name: "Menu Item 02",
            category: "Category A",
            dietaryTags: ["Vegan", "Gluten-Free"],
            allergens: ["Soy"],
            availability: "available",
            studentNote: "Freshly prepared each morning.",
          },
        ],
      },
      {
        id: "st-a2",
        name: "Station B",
        items: [
          {
            id: "it-a2-1",
            name: "Menu Item 03",
            category: "Category B",
            dietaryTags: ["Halal"],
            allergens: ["Eggs"],
            availability: "limited",
          },
        ],
      },
    ],
  },
  {
    id: "menu-a-lunch",
    locationId: "loc-a",
    date: TODAY_ISO,
    mealPeriod: "lunch",
    status: "draft",
    title: "Midday service",
    updatedAt: "35m ago",
    updatedBy: "John Doe",
    stations: [
      {
        id: "st-al1",
        name: "Station A",
        items: [
          {
            id: "it-al1-1",
            name: "Menu Item 04",
            category: "Category B",
            dietaryTags: ["Vegetarian", "Gluten-Free"],
            allergens: ["Tree Nuts"],
            availability: "available",
          },
          {
            id: "it-al1-2",
            name: "Menu Item 05",
            category: "Category C",
            dietaryTags: [],
            allergens: ["Fish"],
            availability: "unavailable",
          },
        ],
      },
    ],
  },
  {
    id: "menu-b-breakfast",
    locationId: "loc-b",
    date: TODAY_ISO,
    mealPeriod: "breakfast",
    status: "draft",
    title: "Morning service",
    updatedAt: "1h ago",
    updatedBy: "John Doe",
    stations: [
      {
        id: "st-bb1",
        name: "Station A",
        items: [
          {
            id: "it-bb1-1",
            name: "Menu Item 06",
            category: "Category C",
            dietaryTags: ["Vegan"],
            allergens: ["Peanuts", "Sesame"],
            availability: "available",
          },
        ],
      },
    ],
  },
  {
    id: "menu-b-lunch",
    locationId: "loc-b",
    date: TODAY_ISO,
    mealPeriod: "lunch",
    status: "needs-attention",
    title: "Midday service",
    internalNotes: "Missing allergen review on one item.",
    updatedAt: "10m ago",
    updatedBy: "System",
    stations: [
      {
        id: "st-bl1",
        name: "Station A",
        items: [
          {
            id: "it-bl1-1",
            name: "Menu Item 07",
            category: "Category D",
            dietaryTags: ["Vegetarian"],
            allergens: ["Milk"],
            availability: "limited",
          },
        ],
      },
      {
        id: "st-bl2",
        name: "Station B",
        items: [],
      },
    ],
  },
  {
    id: "menu-c-dinner",
    locationId: "loc-c",
    date: TODAY_ISO,
    mealPeriod: "dinner",
    status: "published",
    title: "Evening service",
    updatedAt: "4h ago",
    updatedBy: "Jane Doe",
    stations: [
      {
        id: "st-cd1",
        name: "Station A",
        items: [
          {
            id: "it-cd1-1",
            name: "Menu Item 08",
            category: "Category D",
            dietaryTags: ["Halal", "Gluten-Free"],
            allergens: ["Shellfish"],
            availability: "available",
          },
          {
            id: "it-cd1-2",
            name: "Menu Item 09",
            category: "Category A",
            dietaryTags: ["Vegan"],
            allergens: [],
            availability: "available",
          },
        ],
      },
    ],
  },
  {
    id: "menu-d-dinner",
    locationId: "loc-d",
    date: TODAY_ISO,
    mealPeriod: "dinner",
    status: "scheduled",
    title: "Evening service",
    updatedAt: "Yesterday",
    updatedBy: "John Doe",
    stations: [
      {
        id: "st-dd1",
        name: "Station A",
        items: [
          {
            id: "it-dd1-1",
            name: "Menu Item 10",
            category: "Category B",
            dietaryTags: ["Vegetarian"],
            allergens: ["Wheat", "Soy"],
            availability: "available",
          },
        ],
      },
    ],
  },
  {
    id: "menu-e-lunch-tomorrow",
    locationId: "loc-e",
    date: TOMORROW_ISO,
    mealPeriod: "lunch",
    status: "draft",
    title: "Midday service",
    updatedAt: "3h ago",
    updatedBy: "Jane Doe",
    stations: [
      {
        id: "st-el1",
        name: "Station A",
        items: [
          {
            id: "it-el1-1",
            name: "Menu Item 11",
            category: "Category C",
            dietaryTags: ["Gluten-Free"],
            allergens: ["Eggs", "Milk"],
            availability: "available",
          },
        ],
      },
    ],
  },
];
