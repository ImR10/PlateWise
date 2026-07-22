import type {
  AttentionItem as AttentionItemData,
  StatusTone,
} from "../../data/types";
import { Icon } from "../ui/Icon";

const iconToneClass: Record<StatusTone, string> = {
  success: "text-[#1e7e34]",
  warning: "text-yellow-600",
  danger: "text-error",
  neutral: "text-secondary",
  info: "text-secondary",
};

/** A single actionable issue row in the "Needs Attention" panel. */
export function AttentionItem({ item }: { item: AttentionItemData }) {
  return (
    <div className="p-gutter flex items-start gap-3 hover:bg-surface-container transition-colors motion-reduce:transition-none">
      <Icon name={item.icon} className={iconToneClass[item.tone]} />
      <div className="flex-1 min-w-0">
        <p className="font-body-md font-bold">{item.label}</p>
        <p className="text-body-sm text-secondary">{item.detail}</p>
      </div>
      <button
        type="button"
        aria-label={`${item.action}: ${item.label} — ${item.detail}`}
        className="text-primary font-bold text-body-sm hover:underline rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
      >
        {item.action}
      </button>
    </div>
  );
}
