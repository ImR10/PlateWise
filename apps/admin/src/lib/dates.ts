/**
 * Small date helpers for the Menus feature. Dates are handled as plain ISO
 * calendar strings (YYYY-MM-DD) built from local components to avoid timezone
 * drift. `TODAY_ISO` is the mock application's fixed notion of "today" so the
 * UI and tests stay deterministic (there is no real clock dependency).
 */
export const TODAY_ISO = "2024-05-13";

const pad = (n: number): string => String(n).padStart(2, "0");

const toIso = (d: Date): string =>
  `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

const fromIso = (iso: string): Date => {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
};

export const addDaysIso = (iso: string, delta: number): string => {
  const d = fromIso(iso);
  d.setDate(d.getDate() + delta);
  return toIso(d);
};

export const formatDisplayDate = (iso: string): string =>
  fromIso(iso).toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

export const formatShortDate = (iso: string): string =>
  fromIso(iso).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });

export const dayNumber = (iso: string): string =>
  String(fromIso(iso).getDate());
