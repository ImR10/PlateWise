import { useMemo, useState } from "react";

import { Icon } from "../ui/Icon";

export interface SelectionRateRow {
  id: string;
  itemName: string;
  recommendations: number;
  selections: number;
  rate: number;
  changePct: number | null;
  lowVolume: boolean;
}

type SortKey = "itemName" | "recommendations" | "selections" | "rate";

const HEADERS: { key: SortKey; label: string }[] = [
  { key: "itemName", label: "Item" },
  { key: "recommendations", label: "Recommendations" },
  { key: "selections", label: "Estimated selections" },
  { key: "rate", label: "Estimated selection rate" },
];

export function SelectionRateTable({ rows }: { rows: SelectionRateRow[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("recommendations");
  const [asc, setAsc] = useState(false);

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      let cmp: number;
      if (sortKey === "itemName") cmp = a.itemName.localeCompare(b.itemName);
      else cmp = a[sortKey] - b[sortKey];
      return asc ? cmp : -cmp;
    });
    return copy;
  }, [rows, sortKey, asc]);

  const onSort = (key: SortKey) => {
    if (key === sortKey) setAsc((v) => !v);
    else {
      setSortKey(key);
      setAsc(key === "itemName");
    }
  };

  if (rows.length === 0) {
    return (
      <p className="text-body-sm text-secondary py-4 text-center">
        No items match the current filters.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-body-sm min-w-[560px]">
        <caption className="sr-only">
          Estimated recommendation-to-selection performance by item. Sortable.
        </caption>
        <thead>
          <tr className="text-left text-label-md text-secondary uppercase border-b border-outline-variant">
            {HEADERS.map((h) => {
              const active = sortKey === h.key;
              return (
                <th
                  key={h.key}
                  scope="col"
                  aria-sort={
                    active ? (asc ? "ascending" : "descending") : "none"
                  }
                  className="py-2 pr-3 font-semibold"
                >
                  <button
                    type="button"
                    onClick={() => onSort(h.key)}
                    className="inline-flex items-center gap-1 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {h.label}
                    {active ? (
                      <Icon
                        name={asc ? "arrow_upward" : "arrow_downward"}
                        className="text-[14px]"
                      />
                    ) : null}
                  </button>
                </th>
              );
            })}
            <th scope="col" className="py-2 font-semibold">
              Change
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => {
            const change =
              row.changePct === null ? null : Math.round(row.changePct * 100);
            return (
              <tr key={row.id} className="border-b border-outline-variant">
                <th scope="row" className="py-2 pr-3 font-normal">
                  <span className="font-bold">{row.itemName}</span>
                  {row.lowVolume ? (
                    <span className="status-pill badge-neutral ml-2">
                      Low volume
                    </span>
                  ) : null}
                </th>
                <td className="py-2 pr-3 tabular-nums">
                  {row.recommendations.toLocaleString()}
                </td>
                <td className="py-2 pr-3 tabular-nums">
                  {row.selections.toLocaleString()}
                </td>
                <td className="py-2 pr-3 tabular-nums">
                  {row.recommendations > 0
                    ? `${Math.round(row.rate * 100)}%`
                    : "—"}
                </td>
                <td className="py-2 tabular-nums">
                  {change === null ? (
                    <span className="text-secondary">—</span>
                  ) : (
                    <span className="inline-flex items-center gap-1">
                      <Icon
                        name={
                          change > 0
                            ? "arrow_upward"
                            : change < 0
                              ? "arrow_downward"
                              : "remove"
                        }
                        className="text-[14px]"
                      />
                      {change > 0 ? "+" : ""}
                      {change}%
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
