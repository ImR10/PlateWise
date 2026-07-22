/**
 * Managed dining-location domain types for the frontend-only Dining Locations
 * feature. These records are the superset the Menus feature also consumes for
 * its location picker and name resolution. All data is generic mock data held
 * in memory for the session — there is no backend or persistence.
 */
import type { StatusTone } from "./types";
import type { ActivityActor, MealPeriod } from "./menuTypes";

export type LocationStatus = "draft" | "active" | "inactive" | "archived";

export type DayOfWeek =
  | "monday"
  | "tuesday"
  | "wednesday"
  | "thursday"
  | "friday"
  | "saturday"
  | "sunday";

/** Operating hours for a single day (single service window). */
export interface DayHours {
  closed: boolean;
  /** 24h "HH:MM"; only meaningful when not closed. */
  open: string;
  close: string;
}

export type WeeklyHours = Record<DayOfWeek, DayHours>;

/** A service station configured on a dining location. */
export interface LocationStation {
  id: string;
  name: string;
  active: boolean;
}

export interface DiningLocation {
  id: string;
  name: string;
  /** Short student-facing description. */
  description: string;
  /** Longer optional student-facing description. */
  longDescription?: string;
  status: LocationStatus;
  /** Whether the location is shown to students. */
  studentVisible: boolean;
  /** Internal notes — never shown to students / in preview. */
  internalNotes?: string;
  mealPeriods: MealPeriod[];
  stations: LocationStation[];
  hours: WeeklyHours;
  updatedAt: string;
  updatedBy: ActivityActor;
}

export const LOCATION_STATUSES: { value: LocationStatus; label: string }[] = [
  { value: "draft", label: "Draft" },
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "archived", label: "Archived" },
];

export const locationStatusLabel = (value: LocationStatus): string =>
  LOCATION_STATUSES.find((s) => s.value === value)?.label ?? value;

export const locationStatusTone: Record<LocationStatus, StatusTone> = {
  draft: "neutral",
  active: "success",
  inactive: "warning",
  archived: "danger",
};

export const DAYS_OF_WEEK: { value: DayOfWeek; label: string }[] = [
  { value: "monday", label: "Monday" },
  { value: "tuesday", label: "Tuesday" },
  { value: "wednesday", label: "Wednesday" },
  { value: "thursday", label: "Thursday" },
  { value: "friday", label: "Friday" },
  { value: "saturday", label: "Saturday" },
  { value: "sunday", label: "Sunday" },
];

export const dayLabel = (value: DayOfWeek): string =>
  DAYS_OF_WEEK.find((d) => d.value === value)?.label ?? value;

/** A sensible default weekly-hours object (weekdays open, weekend closed). */
export const defaultWeeklyHours = (): WeeklyHours => ({
  monday: { closed: false, open: "07:00", close: "20:00" },
  tuesday: { closed: false, open: "07:00", close: "20:00" },
  wednesday: { closed: false, open: "07:00", close: "20:00" },
  thursday: { closed: false, open: "07:00", close: "20:00" },
  friday: { closed: false, open: "07:00", close: "20:00" },
  saturday: { closed: true, open: "09:00", close: "18:00" },
  sunday: { closed: true, open: "09:00", close: "18:00" },
});
