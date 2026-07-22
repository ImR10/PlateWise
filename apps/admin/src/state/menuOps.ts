/**
 * Pure, immutable transforms over the menu domain. Each function returns a new
 * object graph and never mutates its input, which keeps the reducer trivial and
 * makes the operations easy to test in isolation.
 */
import type {
  AvailabilityStatus,
  Allergen,
  DietaryTag,
  FoodCategory,
  FoodCatalogItem,
  MealPeriod,
  Menu,
  MenuItem,
  MenuStation,
} from "../data/menuTypes";
import { createId } from "../lib/ids";

export interface CreateMenuInput {
  locationId: string;
  date: string;
  mealPeriod: MealPeriod;
  title: string;
}

export interface CustomItemInput {
  name: string;
  category: FoodCategory;
  dietaryTags: DietaryTag[];
  allergens: Allergen[];
  description?: string;
}

/** Stamp a menu as freshly edited this session. */
export const touchMenu = (menu: Menu): Menu => ({
  ...menu,
  updatedAt: "Just now",
  updatedBy: "John Doe",
});

export const buildMenu = (input: CreateMenuInput): Menu => ({
  id: createId("menu"),
  locationId: input.locationId,
  date: input.date,
  mealPeriod: input.mealPeriod,
  status: "draft",
  title: input.title.trim() || "Untitled menu",
  internalNotes: "",
  stations: [{ id: createId("st"), name: "Station A", items: [] }],
  updatedAt: "Just now",
  updatedBy: "John Doe",
});

export const cloneMenu = (menu: Menu): Menu => ({
  ...menu,
  id: createId("menu"),
  title: `${menu.title} (copy)`,
  status: "draft",
  updatedAt: "Just now",
  updatedBy: "John Doe",
  stations: menu.stations.map((station) => ({
    ...station,
    id: createId("st"),
    items: station.items.map((item) => ({ ...item, id: createId("it") })),
  })),
});

export const menuItemFromCatalog = (catalog: FoodCatalogItem): MenuItem => ({
  id: createId("it"),
  name: catalog.name,
  category: catalog.category,
  dietaryTags: [...catalog.dietaryTags],
  allergens: [...catalog.allergens],
  availability: "available",
  catalogId: catalog.id,
});

export const menuItemFromCustom = (input: CustomItemInput): MenuItem => ({
  id: createId("it"),
  name: input.name.trim(),
  category: input.category,
  dietaryTags: [...input.dietaryTags],
  allergens: [...input.allergens],
  availability: "available",
});

/* --- Station transforms --- */

const nextStationName = (menu: Menu): string => {
  const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  for (const letter of letters) {
    const name = `Station ${letter}`;
    if (!menu.stations.some((s) => s.name === name)) return name;
  }
  return `Station ${menu.stations.length + 1}`;
};

export const addStation = (menu: Menu, name?: string): Menu => ({
  ...menu,
  stations: [
    ...menu.stations,
    { id: createId("st"), name: name ?? nextStationName(menu), items: [] },
  ],
});

export const renameStation = (
  menu: Menu,
  stationId: string,
  name: string,
): Menu => ({
  ...menu,
  stations: menu.stations.map((station) =>
    station.id === stationId ? { ...station, name } : station,
  ),
});

export const deleteStation = (menu: Menu, stationId: string): Menu => ({
  ...menu,
  stations: menu.stations.filter((station) => station.id !== stationId),
});

export const moveStation = (
  menu: Menu,
  stationId: string,
  direction: -1 | 1,
): Menu => {
  const index = menu.stations.findIndex((s) => s.id === stationId);
  const target = index + direction;
  if (index < 0 || target < 0 || target >= menu.stations.length) return menu;
  const stations = [...menu.stations];
  [stations[index], stations[target]] = [stations[target], stations[index]];
  return { ...menu, stations };
};

/* --- Item transforms --- */

const mapStation = (
  menu: Menu,
  stationId: string,
  fn: (station: MenuStation) => MenuStation,
): Menu => ({
  ...menu,
  stations: menu.stations.map((station) =>
    station.id === stationId ? fn(station) : station,
  ),
});

export const addItems = (
  menu: Menu,
  stationId: string,
  items: MenuItem[],
): Menu =>
  mapStation(menu, stationId, (station) => ({
    ...station,
    items: [...station.items, ...items],
  }));

export const removeItem = (
  menu: Menu,
  stationId: string,
  itemId: string,
): Menu =>
  mapStation(menu, stationId, (station) => ({
    ...station,
    items: station.items.filter((item) => item.id !== itemId),
  }));

export const updateItem = (
  menu: Menu,
  stationId: string,
  itemId: string,
  patch: Partial<MenuItem>,
): Menu =>
  mapStation(menu, stationId, (station) => ({
    ...station,
    items: station.items.map((item) =>
      item.id === itemId ? { ...item, ...patch } : item,
    ),
  }));

export const setItemAvailability = (
  menu: Menu,
  stationId: string,
  itemId: string,
  availability: AvailabilityStatus,
): Menu => updateItem(menu, stationId, itemId, { availability });

export const moveItem = (
  menu: Menu,
  stationId: string,
  itemId: string,
  direction: -1 | 1,
): Menu =>
  mapStation(menu, stationId, (station) => {
    const index = station.items.findIndex((item) => item.id === itemId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= station.items.length)
      return station;
    const items = [...station.items];
    [items[index], items[target]] = [items[target], items[index]];
    return { ...station, items };
  });

export const moveItemToStation = (
  menu: Menu,
  fromStationId: string,
  itemId: string,
  toStationId: string,
): Menu => {
  if (fromStationId === toStationId) return menu;
  const fromStation = menu.stations.find((s) => s.id === fromStationId);
  const moving = fromStation?.items.find((item) => item.id === itemId);
  if (!moving) return menu;
  return {
    ...menu,
    stations: menu.stations.map((station) => {
      if (station.id === fromStationId) {
        return {
          ...station,
          items: station.items.filter((item) => item.id !== itemId),
        };
      }
      if (station.id === toStationId) {
        return { ...station, items: [...station.items, moving] };
      }
      return station;
    }),
  };
};
