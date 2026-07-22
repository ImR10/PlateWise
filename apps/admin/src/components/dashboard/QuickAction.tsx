import type { QuickAction as QuickActionData } from "../../data/types";
import { Icon } from "../ui/Icon";

/**
 * A dashboard shortcut button. Wired for hover/focus/pressed/disabled states;
 * the actual navigation/mutation behavior arrives in a later milestone.
 */
export function QuickAction({ action }: { action: QuickActionData }) {
  return (
    <button
      type="button"
      disabled={action.disabled}
      className="flex flex-col items-center justify-center p-4 border border-outline-variant rounded hover:bg-surface-container-high hover:border-primary active:scale-95 transition-all motion-reduce:transition-none motion-reduce:active:scale-100 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:border-outline-variant disabled:active:scale-100"
    >
      <Icon
        name={action.icon}
        className="text-primary group-hover:scale-110 transition-transform motion-reduce:transition-none mb-2"
      />
      <span className="text-body-sm font-bold">{action.label}</span>
    </button>
  );
}
