import { useId } from "react";

import type { LocationStation } from "../../data/locationTypes";
import { Button } from "../ui/Button";
import { Icon } from "../ui/Icon";

interface LocationStationsEditorProps {
  stations: LocationStation[];
  onAdd: () => void;
  onRename: (stationId: string, name: string) => void;
  onToggleActive: (stationId: string, active: boolean) => void;
  onMove: (stationId: string, direction: -1 | 1) => void;
  onRemove: (station: LocationStation) => void;
}

export function LocationStationsEditor({
  stations,
  onAdd,
  onRename,
  onToggleActive,
  onMove,
  onRemove,
}: LocationStationsEditorProps) {
  const baseId = useId();

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-h3 text-h3">Stations</h4>
        <Button variant="secondary" icon="add" onClick={onAdd}>
          Add Station
        </Button>
      </div>

      {stations.length === 0 ? (
        <p className="text-body-sm text-secondary">
          No stations yet. Add a station to configure this location.
        </p>
      ) : (
        <ul className="space-y-2">
          {stations.map((station, index) => {
            const nameId = `${baseId}-${station.id}`;
            const invalid = !station.name.trim();
            return (
              <li
                key={station.id}
                className="border border-outline-variant rounded p-3 flex flex-wrap items-center gap-component-gap-sm"
              >
                <div className="flex-1 min-w-[160px]">
                  <label htmlFor={nameId} className="sr-only">
                    Station name
                  </label>
                  <input
                    id={nameId}
                    type="text"
                    value={station.name}
                    aria-invalid={invalid}
                    onChange={(e) => onRename(station.id, e.target.value)}
                    className="w-full rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  />
                </div>
                <label className="flex items-center gap-2 text-body-sm">
                  <input
                    type="checkbox"
                    checked={station.active}
                    onChange={(e) =>
                      onToggleActive(station.id, e.target.checked)
                    }
                  />
                  Active
                </label>
                <Button
                  size="sm"
                  variant="secondary"
                  aria-label={`Move ${station.name || "station"} up`}
                  disabled={index === 0}
                  onClick={() => onMove(station.id, -1)}
                >
                  <Icon name="arrow_upward" className="text-[16px]" />
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  aria-label={`Move ${station.name || "station"} down`}
                  disabled={index === stations.length - 1}
                  onClick={() => onMove(station.id, 1)}
                >
                  <Icon name="arrow_downward" className="text-[16px]" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  icon="delete"
                  aria-label={`Remove ${station.name || "station"}`}
                  onClick={() => onRemove(station)}
                >
                  Remove
                </Button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
