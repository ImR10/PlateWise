/**
 * Initial in-memory managed dining locations (generic placeholders only).
 * This is the seed loaded into the DiningLocations provider at session start;
 * edits live only in React state and reset on refresh.
 */
import { defaultWeeklyHours, type DiningLocation } from "./locationTypes";

/** Generic institution label used in the student-facing previews. */
export const SAMPLE_INSTITUTION = "Sample University";

export const initialDiningLocations: DiningLocation[] = [
  {
    id: "loc-a",
    name: "Dining Hall A",
    description: "All-day dining with rotating stations.",
    longDescription:
      "A full-service dining hall offering breakfast, lunch, and dinner across several stations.",
    status: "active",
    studentVisible: true,
    internalNotes: "Primary location — keep hours current.",
    mealPeriods: ["breakfast", "lunch", "dinner"],
    stations: [
      { id: "loc-a-st-1", name: "Station A", active: true },
      { id: "loc-a-st-2", name: "Station B", active: true },
      { id: "loc-a-st-3", name: "Station C", active: false },
    ],
    hours: defaultWeeklyHours(),
    updatedAt: "2h ago",
    updatedBy: "Jane Doe",
  },
  {
    id: "loc-b",
    name: "Dining Hall B",
    description: "Breakfast and lunch service.",
    status: "active",
    studentVisible: true,
    mealPeriods: ["breakfast", "lunch"],
    stations: [
      { id: "loc-b-st-1", name: "Station A", active: true },
      { id: "loc-b-st-2", name: "Station B", active: true },
    ],
    hours: {
      monday: { closed: false, open: "07:30", close: "14:00" },
      tuesday: { closed: false, open: "07:30", close: "14:00" },
      wednesday: { closed: false, open: "07:30", close: "14:00" },
      thursday: { closed: false, open: "07:30", close: "14:00" },
      friday: { closed: false, open: "07:30", close: "14:00" },
      saturday: { closed: true, open: "09:00", close: "13:00" },
      sunday: { closed: true, open: "09:00", close: "13:00" },
    },
    updatedAt: "5h ago",
    updatedBy: "John Doe",
  },
  {
    id: "loc-c",
    name: "Dining Hall C",
    description: "Lunch and dinner service.",
    status: "draft",
    studentVisible: false,
    internalNotes: "Not yet published to students.",
    mealPeriods: ["lunch", "dinner"],
    stations: [{ id: "loc-c-st-1", name: "Station A", active: true }],
    hours: defaultWeeklyHours(),
    updatedAt: "1d ago",
    updatedBy: "John Doe",
  },
  {
    id: "loc-d",
    name: "Dining Hall D",
    description: "Evening dinner service.",
    status: "inactive",
    studentVisible: false,
    mealPeriods: ["dinner"],
    stations: [{ id: "loc-d-st-1", name: "Station A", active: true }],
    hours: defaultWeeklyHours(),
    updatedAt: "3d ago",
    updatedBy: "System",
  },
  {
    id: "loc-e",
    name: "Dining Hall E",
    description: "Lunch service.",
    status: "archived",
    studentVisible: false,
    mealPeriods: ["lunch"],
    stations: [{ id: "loc-e-st-1", name: "Station A", active: true }],
    hours: defaultWeeklyHours(),
    updatedAt: "2w ago",
    updatedBy: "System",
  },
];
