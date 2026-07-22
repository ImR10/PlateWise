import type { ReactNode } from "react";

import { Icon } from "./Icon";

interface EmptyStateProps {
  icon: string;
  title: string;
  message: string;
  /** Optional action (button or link). */
  action?: ReactNode;
}

/** Centered empty / not-found panel matching the admin card style. */
export function EmptyState({ icon, title, message, action }: EmptyStateProps) {
  return (
    <div className="admin-card p-gutter flex flex-col items-center text-center gap-3 py-12">
      <div className="w-12 h-12 rounded-full bg-primary-fixed text-primary flex items-center justify-center">
        <Icon name={icon} />
      </div>
      <h3 className="font-h3 text-h3">{title}</h3>
      <p className="text-body-sm text-secondary max-w-sm">{message}</p>
      {action}
    </div>
  );
}
