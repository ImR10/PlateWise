import {
  DATA_SOURCE_STATUS_LABEL,
  type DataSourceRow,
  type DataSourceStatus,
} from "../../data/analysisTypes";
import type { StatusTone } from "../../data/types";
import { StatusBadge } from "../ui/StatusBadge";

const statusTone: Record<DataSourceStatus, StatusTone> = {
  "mock-data": "warning",
  "frontend-model": "success",
  "not-connected": "danger",
  "integration-required": "warning",
  "backend-required": "warning",
};

export function DataSourcePanel({ rows }: { rows: DataSourceRow[] }) {
  return (
    <section className="admin-card p-gutter" aria-labelledby="data-sources">
      <h3 id="data-sources" className="font-h3 text-h3">
        Data sources &amp; quality
      </h3>
      <p className="text-body-sm text-secondary mb-3">
        Which future data sources would power these analytics, and their current
        status. This view is intentionally honest: most consumption and
        inventory metrics require backend event tracking and dining-system
        integrations.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-body-sm min-w-[520px]">
          <thead>
            <tr className="text-left text-label-md text-secondary uppercase border-b border-outline-variant">
              <th scope="col" className="py-2 pr-3 font-semibold">
                Data source
              </th>
              <th scope="col" className="py-2 pr-3 font-semibold">
                Status
              </th>
              <th scope="col" className="py-2 font-semibold">
                What it would enable
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b border-outline-variant">
                <th scope="row" className="py-2 pr-3 font-bold font-body-md">
                  {row.label}
                </th>
                <td className="py-2 pr-3">
                  <StatusBadge tone={statusTone[row.status]}>
                    {DATA_SOURCE_STATUS_LABEL[row.status]}
                  </StatusBadge>
                </td>
                <td className="py-2 text-secondary">{row.enables}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
