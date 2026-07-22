import { useId, useState } from "react";

import {
  DATA_QUALITY_LABEL,
  SEVERITY_LABEL,
  SIGNAL_TYPE_LABEL,
  type AnalysisSignal,
  type SignalSeverity,
} from "../../data/analysisTypes";
import type { StatusTone } from "../../data/types";
import { Icon } from "../ui/Icon";
import { StatusBadge } from "../ui/StatusBadge";

const severityTone: Record<SignalSeverity, StatusTone> = {
  info: "neutral",
  watch: "warning",
  risk: "danger",
};

const severityIcon: Record<SignalSeverity, string> = {
  info: "info",
  watch: "visibility",
  risk: "warning",
};

interface SignalCardProps {
  signal: AnalysisSignal;
  itemName: string;
  locationName?: string;
}

export function SignalCard({
  signal,
  itemName,
  locationName,
}: SignalCardProps) {
  const [open, setOpen] = useState(false);
  const detailsId = useId();

  return (
    <div className="admin-card p-gutter flex flex-col gap-2">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h4 className="font-body-md font-bold flex items-center gap-1">
            <Icon
              name={severityIcon[signal.severity]}
              className="text-[18px]"
            />
            {SIGNAL_TYPE_LABEL[signal.type]}
          </h4>
          <p className="text-body-sm text-secondary">
            {itemName}
            {locationName ? ` • ${locationName}` : ""}
          </p>
        </div>
        <StatusBadge tone={severityTone[signal.severity]}>
          {SEVERITY_LABEL[signal.severity]}
        </StatusBadge>
      </div>

      <p className="text-body-sm">{signal.reason}</p>
      <p className="flex items-start gap-1 text-body-sm text-primary">
        <Icon name="lightbulb" className="text-[16px]" />
        <span>Suggested review: {signal.interpretation}</span>
      </p>

      <div className="flex items-center gap-2">
        <span className="status-pill badge-neutral">
          {DATA_QUALITY_LABEL[signal.dataQuality]}
        </span>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls={detailsId}
          className="text-primary font-bold text-body-sm rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          {open ? "Hide details" : "Show details"}
        </button>
      </div>

      {open ? (
        <dl
          id={detailsId}
          className="grid grid-cols-1 sm:grid-cols-2 gap-1 mt-1"
        >
          {signal.metrics.map((m) => (
            <div
              key={m.label}
              className="flex justify-between gap-2 text-body-sm"
            >
              <dt className="text-secondary">{m.label}</dt>
              <dd className="font-bold tabular-nums">{m.value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </div>
  );
}
