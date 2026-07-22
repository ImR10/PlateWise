/**
 * Validation for activating/publishing a dining location. Pure function —
 * returns the list of reasons the location cannot be made active yet.
 */
import { DAYS_OF_WEEK, type DiningLocation } from "../data/locationTypes";

export interface ValidationIssue {
  id: string;
  message: string;
}

export function validateLocationForActivation(
  location: DiningLocation,
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  if (!location.name.trim()) {
    issues.push({ id: "name", message: "Enter a location name." });
  }
  if (location.mealPeriods.length === 0) {
    issues.push({
      id: "meal-periods",
      message: "Select at least one supported meal period.",
    });
  }
  if (!location.stations.some((station) => station.active)) {
    issues.push({
      id: "stations",
      message: "Add at least one active station.",
    });
  }
  if (location.stations.some((station) => !station.name.trim())) {
    issues.push({
      id: "station-names",
      message: "Give every station a name.",
    });
  }

  // Operating-hours consistency for any open day.
  for (const { value, label } of DAYS_OF_WEEK) {
    const day = location.hours[value];
    if (day.closed) continue;
    if (!day.open || !day.close) {
      issues.push({
        id: `hours-${value}`,
        message: `${label} is open but is missing an opening or closing time.`,
      });
    } else if (day.close <= day.open) {
      issues.push({
        id: `hours-order-${value}`,
        message: `${label} closing time must be later than its opening time.`,
      });
    }
  }

  return issues;
}
