/**
 * Publish-time validation for a menu. Pure function — returns the list of
 * reasons a menu cannot be published yet (empty list means it is publishable).
 */
import type { Menu, MenuValidationIssue } from "../data/menuTypes";

export function validateMenuForPublish(menu: Menu): MenuValidationIssue[] {
  const issues: MenuValidationIssue[] = [];

  if (!menu.locationId) {
    issues.push({
      id: "location",
      field: "location",
      message: "Select a dining location.",
    });
  }
  if (!menu.date) {
    issues.push({ id: "date", field: "date", message: "Select a date." });
  }
  if (!menu.mealPeriod) {
    issues.push({
      id: "mealPeriod",
      field: "mealPeriod",
      message: "Select a meal period.",
    });
  }

  if (menu.stations.length === 0) {
    issues.push({
      id: "no-station",
      message: "Add at least one station before publishing.",
    });
    return issues;
  }

  // Blank station names.
  menu.stations.forEach((station) => {
    if (!station.name.trim()) {
      issues.push({
        id: `station-name-${station.id}`,
        stationId: station.id,
        field: "station-name",
        message: "Give every station a name.",
      });
    }
    // Blank item display names.
    station.items.forEach((item) => {
      if (!item.name.trim()) {
        issues.push({
          id: `item-name-${item.id}`,
          stationId: station.id,
          itemId: item.id,
          field: "item-name",
          message: "Give every item a display name.",
        });
      }
    });
  });

  const allItems = menu.stations.flatMap((station) => station.items);

  if (allItems.length === 0) {
    issues.push({
      id: "all-empty",
      message: "Add at least one item — all stations are currently empty.",
    });
  } else if (
    !allItems.some(
      (item) =>
        item.availability === "available" || item.availability === "limited",
    )
  ) {
    issues.push({
      id: "none-available",
      message: "At least one item must be Available or Limited.",
    });
  }

  return issues;
}
