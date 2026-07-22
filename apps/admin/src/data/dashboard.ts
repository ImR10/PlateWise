/**
 * Local mock data for the PlateWise Admin dashboard (University of Georgia).
 *
 * This is the single data boundary for the dashboard milestone. Every value
 * the UI shows lives here rather than being scattered through JSX, so it can
 * later be swapped for API calls (e.g. a `useDashboard()` hook backed by the
 * shared FastAPI service) without touching the presentational components.
 *
 * Scope note: PlateWise Admin manages one university. Only University of
 * Georgia dining locations appear here — no other institutions, and no
 * platform-wide or multi-university data.
 */
import type {
  ActivityEntry,
  AttentionItem,
  DiningLocation,
  Institution,
  NavItem,
  QuickAction,
  StaffProfile,
  TodaySummary,
  UpcomingMenu,
} from "./types";

export const institution: Institution = {
  name: "University of Georgia",
  shortCode: "UGA",
};

export const staffProfile: StaffProfile = {
  name: "John Doe",
  role: "Dining Menu Coordinator",
  initials: "JD",
};

/** The date shown in the header, matching the approved design. */
export const currentDate = "October 24, 2023";

export const navItems: NavItem[] = [
  { label: "Dashboard", icon: "dashboard", path: "/dashboard" },
  { label: "Menus", icon: "restaurant_menu", path: "/menus" },
  { label: "Dining Locations", icon: "location_on", path: "/locations" },
  { label: "Food Catalog", icon: "inventory_2", path: "/foods" },
  { label: "Activity", icon: "history", path: "/activity" },
  { label: "Settings", icon: "settings", path: "/settings" },
];

export const todaySummary: TodaySummary = {
  heading: "Are today's menus ready?",
  summary:
    "2 tasks remaining • 3 dining locations ready • 1 dining location needs review",
  meals: [
    {
      id: "breakfast",
      meal: "Breakfast",
      statusLabel: "Published",
      tone: "success",
      accent: "#1e7e34",
    },
    {
      id: "lunch",
      meal: "Lunch",
      statusLabel: "Needs Review",
      tone: "warning",
      accent: "#d97706",
    },
    {
      id: "dinner",
      meal: "Dinner",
      statusLabel: "Draft",
      tone: "neutral",
      accent: "#94a3b8",
    },
    {
      id: "late-night",
      meal: "Late Night",
      statusLabel: "Not Started",
      tone: "danger",
      accent: "#dc2626",
    },
  ],
};

export const attentionItems: AttentionItem[] = [
  {
    id: "chicken-alfredo-allergens",
    label: "Missing Allergy Info",
    detail: "Chicken Alfredo • Bolton",
    icon: "error",
    tone: "danger",
    action: "Fix",
  },
  {
    id: "bolton-dinner-unpublished",
    label: "Menu Not Published",
    detail: "Dinner • Bolton",
    icon: "warning",
    tone: "warning",
    action: "Review",
  },
  {
    id: "missing-calories",
    label: "Missing Calories",
    detail: "3 items total",
    icon: "info",
    tone: "info",
    action: "Fix",
  },
  {
    id: "village-summit-duplicate",
    label: "Duplicate Detected",
    detail: "Village Summit",
    icon: "content_copy",
    tone: "warning",
    action: "Review",
  },
];

export const diningLocations: DiningLocation[] = [
  {
    id: "bolton",
    name: "Bolton Dining Commons",
    statusLabel: "1 issue",
    tone: "danger",
    lastUpdated: "10m ago",
    readiness: "Draft",
  },
  {
    id: "snelling",
    name: "Snelling Dining Commons",
    statusLabel: "Clean",
    tone: "success",
    lastUpdated: "2h ago",
    readiness: "Published",
  },
  {
    id: "village-summit",
    name: "Village Summit",
    statusLabel: "2 issues",
    tone: "warning",
    lastUpdated: "45m ago",
    readiness: "In Review",
  },
  {
    id: "oglethorpe",
    name: "Oglethorpe Dining Commons",
    statusLabel: "Clean",
    tone: "success",
    lastUpdated: "5h ago",
    readiness: "Published",
  },
];

export const upcomingMenus: UpcomingMenu[] = [
  {
    id: "wed",
    day: "25",
    label: "Tomorrow (Wed)",
    statusLabel: "Draft",
    tone: "neutral",
  },
  {
    id: "fri",
    day: "26",
    label: "Friday",
    statusLabel: "Published",
    tone: "success",
  },
  {
    id: "sat",
    day: "27",
    label: "Saturday",
    statusLabel: "Not Started",
    tone: "danger",
  },
  {
    id: "sun",
    day: "28",
    label: "Sunday",
    statusLabel: "Not Started",
    tone: "danger",
  },
];

export const recentActivity: ActivityEntry[] = [
  {
    id: "act-1",
    initials: "JD",
    actor: "John Doe",
    description: "updated Chicken Alfredo",
    timestamp: "34 minutes ago",
  },
  {
    id: "act-2",
    initials: "JD",
    actor: "Jane Doe",
    description: "published Bolton lunch menu",
    timestamp: "2 hours ago",
  },
  {
    id: "act-3",
    initials: "SY",
    actor: "System",
    description: "flagged duplicate entry at Village Summit",
    timestamp: "Yesterday at 4:12 PM",
  },
  {
    id: "act-4",
    initials: "JD",
    actor: "Jane Doe",
    description: "added 12 new items to Food Catalog",
    timestamp: "Yesterday at 11:30 AM",
  },
];

export const quickActions: QuickAction[] = [
  { id: "create-menu", label: "Create Menu", icon: "add_circle" },
  { id: "todays-menu", label: "Today's Menu", icon: "edit_calendar" },
  { id: "add-food", label: "Add Food", icon: "fastfood" },
  { id: "copy-previous", label: "Copy Previous", icon: "content_copy" },
  { id: "publish-menu", label: "Publish Menu", icon: "publish" },
];
