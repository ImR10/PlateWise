export interface StatTile {
  label: string;
  value: number;
  accent: string;
}

/** A responsive row of derived summary count tiles. */
export function StatTiles({ tiles }: { tiles: StatTile[] }) {
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
