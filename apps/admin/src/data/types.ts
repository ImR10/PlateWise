/**
 * Shared domain types for the PlateWise Admin dashboard.
 *
 * These describe the shape of the data the dashboard renders. For this
 * milestone they are populated by the local mock module in `dashboard.ts`;
 * the same interfaces are intended to be satisfied later by real API
 * responses without changing the presentational components.
 */

/** Visual tone shared by status pills and issue icons. */
export type StatusTone = "success" | "warning" | "danger" | "neutral" | "info";

/** A meal service and its publish readiness for the current day. */
export interface MealStatus {
  id: string;
  meal: string;
  statusLabel: string;
  tone: StatusTone;
  /** Hex accent used for the vertical color bar in the design. */
  accent: string;
}

/** An actionable issue surfaced in the "Needs Attention" panel. */
export interface AttentionItem {
  id: string;
  label: string;
  /** Affected food/menu, and location when relevant. */
  detail: string;
  /** Material Symbols icon name. */
  icon: string;
  tone: StatusTone;
  action: "Fix" | "Review";
}

/** A University of Georgia dining location and its menu readiness. */
export interface DiningLocation {
  id: string;
  name: string;
  /** e.g. "Clean", "1 issue", "2 issues". */
  statusLabel: string;
  tone: StatusTone;
  lastUpdated: string;
  readiness: string;
}

/** A day of upcoming menu preparation. */
export interface UpcomingMenu {
  id: string;
  /** Day-of-month number shown in the compact date chip. */
  day: string;
  label: string;
  statusLabel: string;
  tone: StatusTone;
}

/** A single entry in the recent activity feed. */
export interface ActivityEntry {
  id: string;
  initials: string;
  actor: string;
  description: string;
  timestamp: string;
}

/** A dashboard quick action shortcut. */
export interface QuickAction {
  id: string;
  label: string;
  icon: string;
  /** Present but disabled where the action has no backend yet. */
  disabled?: boolean;
}

/** A primary navigation destination in the sidebar. */
export interface NavItem {
  label: string;
  icon: string;
  path: string;
}

/** The institution this admin console manages (single university). */
export interface Institution {
  name: string;
  shortCode: string;
}

/** Headline readiness summary for today's menus. */
export interface TodaySummary {
  heading: string;
  summary: string;
  meals: MealStatus[];
}

/** The signed-in staff member shown in the sidebar. */
export interface StaffProfile {
  name: string;
  role: string;
  initials: string;
}
