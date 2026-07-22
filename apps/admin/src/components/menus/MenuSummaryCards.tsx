import type { Menu } from "../../data/menuTypes";

interface MenuSummaryCardsProps {
  /** Menus for the selected date (before filters are applied). */
  menus: Menu[];
}

/** Derived count tiles for the selected date. */
export function MenuSummaryCards({ menus }: MenuSummaryCardsProps) {
  const total = menus.length;
  const published = menus.filter((m) => m.status === "published").length;
  const drafts = menus.filter((m) => m.status === "draft").length;
  const needsAttention = menus.filter(
    (m) => m.status === "needs-attention",
  ).length;

  const tiles = [
    { label: "Total Menus", value: total, accent: "#5b4040" },
    { label: "Published", value: published, accent: "#1e7e34" },
    { label: "Drafts", value: drafts, accent: "#94a3b8" },
    { label: "Needs Attention", value: needsAttention, accent: "#d97706" },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-component-gap-md">
      {tiles.map((tile) => (
        <div
          key={tile.label}
          className="admin-card p-gutter flex items-center gap-3"
        >
          <div
            className="w-2 h-10 rounded shrink-0"
            style={{ backgroundColor: tile.accent }}
            aria-hidden="true"
          />
          <div>
            <p className="font-h2 text-h2">{tile.value}</p>
            <p className="text-label-md text-secondary uppercase">
              {tile.label}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
