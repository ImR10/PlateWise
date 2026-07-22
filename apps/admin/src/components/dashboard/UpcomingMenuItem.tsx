import type { UpcomingMenu } from "../../data/types";
import { StatusBadge } from "../ui/StatusBadge";

/** A single upcoming-day row (date chip, label, status). */
export function UpcomingMenuItem({ menu }: { menu: UpcomingMenu }) {
  return (
    <div className="flex justify-between items-center gap-3 py-2">
      <div className="flex items-center gap-3">
        <span className="w-8 h-8 rounded bg-surface-container flex items-center justify-center font-bold text-xs shrink-0">
          {menu.day}
        </span>
        <span className="font-body-md">{menu.label}</span>
      </div>
      <StatusBadge tone={menu.tone}>{menu.statusLabel}</StatusBadge>
    </div>
  );
}
