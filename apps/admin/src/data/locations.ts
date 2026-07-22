/**
 * Generic dining-location mock data for the Menus feature.
 * No real institutions or dining halls — placeholders only.
 */
import type { DiningLocation } from "./menuTypes";

/** Generic institution label used in the student-facing preview. */
export const SAMPLE_INSTITUTION = "Sample University";

export const diningLocations: DiningLocation[] = [
  { id: "loc-a", name: "Dining Hall A" },
  { id: "loc-b", name: "Dining Hall B" },
  { id: "loc-c", name: "Dining Hall C" },
  { id: "loc-d", name: "Dining Hall D" },
  { id: "loc-e", name: "Dining Hall E" },
];

export const diningLocationName = (id: string): string =>
  diningLocations.find((loc) => loc.id === id)?.name ?? "Unassigned Location";
