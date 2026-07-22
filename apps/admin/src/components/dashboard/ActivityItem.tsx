import type { ActivityEntry } from "../../data/types";

/** A single entry in the recent activity feed. */
export function ActivityItem({ entry }: { entry: ActivityEntry }) {
  return (
    <div className="flex gap-3">
      <div
        className="w-8 h-8 rounded-full bg-surface-container-high flex items-center justify-center font-bold text-[10px] shrink-0"
        aria-hidden="true"
      >
        {entry.initials}
      </div>
      <div>
        <p className="text-body-sm">
          <span className="font-bold">{entry.actor}</span> {entry.description}
        </p>
        <p className="text-[11px] text-secondary">{entry.timestamp}</p>
      </div>
    </div>
  );
}
