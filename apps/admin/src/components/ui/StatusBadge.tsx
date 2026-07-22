import type { ReactNode } from "react";

import type { StatusTone } from "../../data/types";

const toneClass: Record<StatusTone, string> = {
  success: "badge-success",
  warning: "badge-warning",
  danger: "badge-danger",
  neutral: "badge-neutral",
  info: "badge-neutral",
};

interface StatusBadgeProps {
  tone: StatusTone;
  children: ReactNode;
}

/** Small uppercase status pill used across the dashboard. */
export function StatusBadge({ tone, children }: StatusBadgeProps) {
  return <span className={`status-pill ${toneClass[tone]}`}>{children}</span>;
}
