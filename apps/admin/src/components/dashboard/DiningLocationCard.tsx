import { Link } from "react-router-dom";

import type { DiningLocation } from "../../data/types";
import { Icon } from "../ui/Icon";
import { StatusBadge } from "../ui/StatusBadge";

/** A Sample University dining location summary card. */
export function DiningLocationCard({ location }: { location: DiningLocation }) {
  return (
    <Link
      to="/locations"
      className="admin-card p-3 block hover:border-primary transition-colors motion-reduce:transition-none group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
    >
      <div className="flex justify-between items-start gap-2">
        <p className="font-body-md font-bold group-hover:text-primary transition-colors motion-reduce:transition-none">
          {location.name}
        </p>
        <StatusBadge tone={location.tone}>{location.statusLabel}</StatusBadge>
      </div>
      <div className="flex items-center justify-between text-body-sm text-secondary mt-4">
        <span className="flex items-center gap-1">
          <Icon name="schedule" className="text-[14px]" />
          {location.lastUpdated}
        </span>
        <span className="text-label-md uppercase">{location.readiness}</span>
      </div>
    </Link>
  );
}
