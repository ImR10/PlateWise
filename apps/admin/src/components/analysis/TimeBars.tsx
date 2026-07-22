export interface TimePoint {
  date: string;
  value: number;
}

interface TimeBarsProps {
  title: string;
  description: string;
  points: TimePoint[];
  valueLabel: string;
}

/**
 * Compact time-series bar strip. Bars are decorative (aria-hidden); a
 * visually-hidden data table provides the accessible equivalent.
 */
export function TimeBars({
  title,
  description,
  points,
  valueLabel,
}: TimeBarsProps) {
  const max = Math.max(1, ...points.map((p) => p.value));
  const first = points[0]?.date;
  const last = points[points.length - 1]?.date;

  return (
    <section className="admin-card p-gutter" aria-labelledby="time-bars">
      <h3 id="time-bars" className="font-h3 text-h3">
        {title}
      </h3>
      <p className="text-body-sm text-secondary mb-3">{description}</p>

      {points.length === 0 ? (
        <p className="text-body-sm text-secondary py-4 text-center">
          No data for the current filters.
        </p>
      ) : (
        <>
          <div
            className="flex items-end gap-0.5 h-28"
            aria-hidden="true"
            role="presentation"
          >
            {points.map((p) => (
              <div
                key={p.date}
                className="flex-1 bg-primary rounded-t min-w-[2px]"
                style={{ height: `${Math.max(3, (p.value / max) * 100)}%` }}
                title={`${p.date}: ${p.value}`}
              />
            ))}
          </div>
          {first && last ? (
            <div className="flex justify-between text-[11px] text-secondary mt-1">
              <span>{first}</span>
              <span>{last}</span>
            </div>
          ) : null}
          <div className="sr-only">
            <table>
              <caption>{`${title}. ${description}`}</caption>
              <thead>
                <tr>
                  <th scope="col">Date</th>
                  <th scope="col">{valueLabel}</th>
                </tr>
              </thead>
              <tbody>
                {points.map((p) => (
                  <tr key={p.date}>
                    <th scope="row">{p.date}</th>
                    <td>{p.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
