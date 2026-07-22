import { Icon } from "../ui/Icon";

interface MetricCardProps {
  title: string;
  value: string;
  caption?: string;
  /** Short accessible explanation of what the metric means. */
  description: string;
  estimated?: boolean;
  change?: { pct: number | null; comparisonLabel: string };
}

function ChangeIndicator({
  pct,
  comparisonLabel,
}: {
  pct: number | null;
  comparisonLabel: string;
}) {
  if (pct === null) {
    return (
      <p className="text-body-sm text-secondary">
        No comparison data available.
      </p>
    );
  }
  const rounded = Math.round(pct * 100);
  const direction = rounded > 0 ? "up" : rounded < 0 ? "down" : "flat";
  const word =
    direction === "up"
      ? "higher"
      : direction === "down"
        ? "lower"
        : "no change";
  const icon =
    direction === "up"
      ? "arrow_upward"
      : direction === "down"
        ? "arrow_downward"
        : "remove";
  return (
    <p className="flex items-center gap-1 text-body-sm">
      <Icon name={icon} className="text-[16px]" />
      <span className="font-bold">
        {rounded > 0 ? "+" : ""}
        {rounded}%
      </span>
      <span className="text-secondary">
        {word} vs {comparisonLabel}
      </span>
    </p>
  );
}

/** A summary metric tile with value, comparison, and an estimated indicator. */
export function MetricCard({
  title,
  value,
  caption,
  description,
  estimated,
  change,
}: MetricCardProps) {
  return (
    <div className="admin-card p-gutter flex flex-col gap-1">
      <div className="flex items-start justify-between gap-2">
        <p className="text-label-md text-secondary uppercase">{title}</p>
        {estimated ? (
          <span className="status-pill badge-neutral shrink-0">Estimated</span>
        ) : null}
      </div>
      <p className="font-h1 text-h1">{value}</p>
      {caption ? (
        <p className="text-body-sm text-secondary">{caption}</p>
      ) : null}
      {change ? <ChangeIndicator {...change} /> : null}
      <p className="text-body-sm text-secondary mt-1">{description}</p>
    </div>
  );
}
