/**
 * Pure, immutable transforms over the dining-location domain. Each function
 * returns a new object and never mutates its input.
 */
import {
  defaultWeeklyHours,
  type DayHours,
  type DayOfWeek,
  type DiningLocation,
} from "../data/locationTypes";
import type { MealPeriod } from "../data/menuTypes";
import { createId } from "../lib/ids";

/** Stamp a location as edited this session. */
export const touchLocation = (location: DiningLocation): DiningLocation => ({
  ...location,
  updatedAt: "Just now",
  updatedBy: "John Doe",
});

export const buildLocation = (): DiningLocation => ({
  id: createId("loc"),
  name: "",
  description: "",
  status: "draft",
  studentVisible: false,
  internalNotes: "",
  mealPeriods: [],
  stations: [{ id: createId("locst"), name: "Station A", active: true }],
  hours: defaultWeeklyHours(),
  updatedAt: "Just now",
  updatedBy: "John Doe",
});

export const cloneLocation = (location: DiningLocation): DiningLocation => ({
  ...location,
  id: createId("loc"),
  name: `${location.name} (copy)`,
  status: "draft",
  updatedAt: "Just now",
  updatedBy: "John Doe",
  stations: location.stations.map((station) => ({
    ...station,
    id: createId("locst"),
  })),
  hours: { ...location.hours },
});

const nextStationName = (location: DiningLocation): string => {
  const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  for (const letter of letters) {
    const name = `Station ${letter}`;
    if (!location.stations.some((s) => s.name === name)) return name;
  }
  return `Station ${location.stations.length + 1}`;
};

export const addStation = (location: DiningLocation): DiningLocation => ({
  ...location,
  stations: [
    ...location.stations,
    { id: createId("locst"), name: nextStationName(location), active: true },
  ],
});

export const renameStation = (
  location: DiningLocation,
  stationId: string,
  name: string,
): DiningLocation => ({
  ...location,
  stations: location.stations.map((station) =>
    station.id === stationId ? { ...station, name } : station,
  ),
});

export const setStationActive = (
  location: DiningLocation,
  stationId: string,
  active: boolean,
): DiningLocation => ({
  ...location,
  stations: location.stations.map((station) =>
    station.id === stationId ? { ...station, active } : station,
  ),
});

export const removeStation = (
  location: DiningLocation,
  stationId: string,
): DiningLocation => ({
  ...location,
  stations: location.stations.filter((station) => station.id !== stationId),
});

export const moveStation = (
  location: DiningLocation,
  stationId: string,
  direction: -1 | 1,
): DiningLocation => {
  const index = location.stations.findIndex((s) => s.id === stationId);
  const target = index + direction;
  if (index < 0 || target < 0 || target >= location.stations.length)
    return location;
  const stations = [...location.stations];
  [stations[index], stations[target]] = [stations[target], stations[index]];
  return { ...location, stations };
};

export const toggleMealPeriod = (
  location: DiningLocation,
  mealPeriod: MealPeriod,
): DiningLocation => ({
  ...location,
  mealPeriods: location.mealPeriods.includes(mealPeriod)
    ? location.mealPeriods.filter((mp) => mp !== mealPeriod)
    : [...location.mealPeriods, mealPeriod],
});

export const updateDayHours = (
  location: DiningLocation,
  day: DayOfWeek,
  patch: Partial<DayHours>,
): DiningLocation => ({
  ...location,
  hours: { ...location.hours, [day]: { ...location.hours[day], ...patch } },
});
