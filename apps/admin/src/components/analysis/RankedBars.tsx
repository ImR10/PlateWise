export interface RankedBarRow {
  id: string;
  label: string;
  value: number;
  /** Optional secondary text shown after the value (e.g. a rate). */
  secondary?: string;
}

interface RankedBarsProps {
  title: string;
  description: string;
  rows: RankedBarRow[];
  valueLabel: string;
  emptyMessage?: string;
}

/**
 * Accessible ranked horizontal-bar chart backed by a real data table. The bars
 * are decorative (aria-hidden); the numeric value text is the accessible
 * representation, so nothing relies on color alone.
 */
export function RankedBars({
  title,
  description,
  rows,
  valueLabel,
  emptyMessage = "No data for the current filters.",
}: RankedBarsProps) {
  const max = Math.max(1, ...rows.map((r) => r.value));

  return (
    <section className="admin-card p-gutter" aria-labelledby={`rb-${title}`}>
      <h3 id={`rb-${title}`} className="font-h3 text-h3">
        {title}
      </h3>
      <p className="text-body-sm text-secondary mb-3">{description}</p>
      {rows.length === 0 ? (
        <p className="text-body-sm text-secondary py-4 text-center">
          {emptyMessage}
        </p>
      ) : (
        <table className="w-full border-collapse">
          <caption className="sr-only">{`${title}. ${description}`}</caption>
          <thead>
            <tr className="text-left text-label-md text-secondary uppercase">
              <th scope="col" className="py-1 pr-3 font-semibold">
                Item
              </th>
              <th scope="col" className="py-1 font-semibold">
                {valueLabel}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="align-middle">
                <th
                  scope="row"
                  className="py-1 pr-3 font-body-md font-normal whitespace-nowrap"
                >
                  {row.label}
                </th>
                <td className="py-1 w-full">
                  <div className="flex items-center gap-2">
                    <div
                      className="flex-1 min-w-0 h-3 rounded bg-surface-container-high"
                      aria-hidden="true"
                    >
                      <div
                        className="h-3 rounded bg-primary"
                        style={{
                          width: `${Math.max(2, (row.value / max) * 100)}%`,
                        }}
                      />
                    </div>
                    <span className="w-14 shrink-0 text-right text-body-sm font-bold tabular-nums">
                      {row.value.toLocaleString()}
                    </span>
                    {row.secondary ? (
                      <span className="hidden md:inline shrink-0 text-body-sm text-secondary">
                        {row.secondary}
                      </span>
                    ) : null}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
