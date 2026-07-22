import { useId } from "react";

import type {
  AvailabilityStatus,
  MenuItem,
  MenuStation,
} from "../../data/menuTypes";
import { Button } from "../ui/Button";
import { Icon } from "../ui/Icon";
import { MenuItemRow } from "./MenuItemRow";

interface StationOption {
  id: string;
  name: string;
}

interface MenuStationSectionProps {
  station: MenuStation;
  index: number;
  count: number;
  stations: StationOption[];
  collapsed: boolean;
  onToggleCollapse: () => void;
  onRename: (name: string) => void;
  onDelete: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onAddItem: () => void;
  onUpdateItem: (itemId: string, patch: Partial<MenuItem>) => void;
  onSetItemAvailability: (
    itemId: string,
    availability: AvailabilityStatus,
  ) => void;
  onMoveItem: (itemId: string, direction: -1 | 1) => void;
  onMoveItemToStation: (itemId: string, toStationId: string) => void;
  onRemoveItem: (itemId: string) => void;
}

export function MenuStationSection({
  station,
  index,
  count,
  stations,
  collapsed,
  onToggleCollapse,
  onRename,
  onDelete,
  onMoveUp,
  onMoveDown,
  onAddItem,
  onUpdateItem,
  onSetItemAvailability,
  onMoveItem,
  onMoveItemToStation,
  onRemoveItem,
}: MenuStationSectionProps) {
  const bodyId = useId();
  const nameInvalid = !station.name.trim();

  return (
    <section className="admin-card">
      <div className="p-gutter flex flex-wrap items-center gap-component-gap-sm border-b border-outline-variant">
        <button
          type="button"
          onClick={onToggleCollapse}
          aria-expanded={!collapsed}
          aria-controls={bodyId}
          aria-label={collapsed ? "Expand station" : "Collapse station"}
          className="text-secondary hover:text-primary rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <Icon name={collapsed ? "chevron_right" : "expand_more"} />
        </button>

        <div className="flex-1 min-w-[160px]">
          <label htmlFor={`${bodyId}-name`} className="sr-only">
            Station name
          </label>
          <input
            id={`${bodyId}-name`}
            type="text"
            value={station.name}
            aria-invalid={nameInvalid}
            onChange={(e) => onRename(e.target.value)}
            className="w-full font-h3 text-h3 bg-transparent rounded px-1 py-0.5 border border-transparent hover:border-outline-variant focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          />
        </div>

        <span className="text-body-sm text-secondary">
          {station.items.length} item{station.items.length === 1 ? "" : "s"}
        </span>

        <div className="flex items-center gap-1">
          <Button
            size="sm"
            variant="secondary"
            aria-label={`Move ${station.name || "station"} up`}
            disabled={index === 0}
            onClick={onMoveUp}
          >
            <Icon name="arrow_upward" className="text-[16px]" />
          </Button>
          <Button
            size="sm"
            variant="secondary"
            aria-label={`Move ${station.name || "station"} down`}
            disabled={index === count - 1}
            onClick={onMoveDown}
          >
            <Icon name="arrow_downward" className="text-[16px]" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            icon="delete"
            aria-label={`Delete ${station.name || "station"}`}
            onClick={onDelete}
          >
            Delete
          </Button>
        </div>
      </div>

      {!collapsed ? (
        <div id={bodyId} className="p-gutter space-y-3">
          {nameInvalid ? (
            <p className="text-body-sm text-error">
              This station needs a name before the menu can be published.
            </p>
          ) : null}

          {station.items.length === 0 ? (
            <p className="text-body-sm text-secondary">
              No items in this station yet.
            </p>
          ) : (
            <ul className="space-y-3">
              {station.items.map((item, itemIndex) => (
                <MenuItemRow
                  key={item.id}
                  item={item}
                  index={itemIndex}
                  count={station.items.length}
                  currentStationId={station.id}
                  stations={stations}
                  onUpdate={(patch) => onUpdateItem(item.id, patch)}
                  onSetAvailability={(a) => onSetItemAvailability(item.id, a)}
                  onMoveUp={() => onMoveItem(item.id, -1)}
                  onMoveDown={() => onMoveItem(item.id, 1)}
                  onMoveToStation={(toStationId) =>
                    onMoveItemToStation(item.id, toStationId)
                  }
                  onRemove={() => onRemoveItem(item.id)}
                />
              ))}
            </ul>
          )}

          <Button variant="secondary" icon="add" onClick={onAddItem}>
            Add Food Item
          </Button>
        </div>
      ) : null}
    </section>
  );
}
