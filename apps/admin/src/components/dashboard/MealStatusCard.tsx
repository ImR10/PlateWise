import type { MealStatus } from "../../data/types";
import { StatusBadge } from "../ui/StatusBadge";

/** One meal service (Breakfast, Lunch, …) with its publish status. */
export function MealStatusCard({ meal }: { meal: MealStatus }) {
  return (
    <div className="p-3 border border-outline-variant rounded bg-surface-container-low flex items-center gap-3">
      <div
        className="w-2 h-10 rounded shrink-0"
        style={{ backgroundColor: meal.accent }}
        aria-hidden="true"
      />
      <div>
        <p className="text-label-md text-secondary uppercase">{meal.meal}</p>
        <StatusBadge tone={meal.tone}>{meal.statusLabel}</StatusBadge>
      </div>
    </div>
  );
}
