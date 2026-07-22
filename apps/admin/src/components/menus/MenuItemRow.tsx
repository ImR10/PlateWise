import { useId, useState } from "react";

import {
  ALLERGENS,
  AVAILABILITY_OPTIONS,
  DIETARY_TAGS,
  FOOD_CATEGORIES,
  availabilityTone,
  type Allergen,
  type AvailabilityStatus,
  type DietaryTag,
  type FoodCategory,
  type MenuItem,
} from "../../data/menuTypes";
import { Button } from "../ui/Button";
import { Icon } from "../ui/Icon";
import { StatusBadge } from "../ui/StatusBadge";

interface StationOption {
  id: string;
  name: string;
}

interface MenuItemRowProps {
  item: MenuItem;
  index: number;
  count: number;
  currentStationId: string;
  stations: StationOption[];
  onUpdate: (patch: Partial<MenuItem>) => void;
  onSetAvailability: (availability: AvailabilityStatus) => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onMoveToStation: (toStationId: string) => void;
  onRemove: () => void;
}

const fieldClass =
  "w-full rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary";

function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value)
    ? list.filter((entry) => entry !== value)
    : [...list, value];
}

export function MenuItemRow({
  item,
  index,
  count,
  currentStationId,
  stations,
  onUpdate,
  onSetAvailability,
  onMoveUp,
  onMoveDown,
  onMoveToStation,
  onRemove,
}: MenuItemRowProps) {
  const [editing, setEditing] = useState(false);
  const nameId = useId();
  const noteId = useId();
  const moveId = useId();
  const otherStations = stations.filter((s) => s.id !== currentStationId);
  const nameInvalid = !item.name.trim();

  return (
    <li className="border border-outline-variant rounded p-3 bg-surface-container-lowest">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-body-md font-bold">
            {item.name.trim() || "Untitled item"}
          </p>
          <p className="text-body-sm text-secondary">{item.category}</p>
        </div>
        <StatusBadge tone={availabilityTone[item.availability]}>
          {AVAILABILITY_OPTIONS.find((a) => a.value === item.availability)
            ?.label ?? item.availability}
        </StatusBadge>
      </div>

      {item.dietaryTags.length > 0 || item.allergens.length > 0 ? (
        <div className="flex flex-wrap gap-1 mt-2">
          {item.dietaryTags.map((tag) => (
            <span
              key={tag}
              className="text-[11px] font-bold px-2 py-0.5 rounded bg-secondary-container text-on-secondary-container"
            >
              {tag}
            </span>
          ))}
          {item.allergens.map((allergen) => (
            <span
              key={allergen}
              className="text-[11px] font-bold px-2 py-0.5 rounded bg-error-container text-on-error-container"
            >
              <span className="sr-only">Contains </span>
              {allergen}
            </span>
          ))}
        </div>
      ) : null}

      {item.studentNote ? (
        <p className="text-body-sm text-secondary mt-2 italic">
          {item.studentNote}
        </p>
      ) : null}

      {/* Availability control */}
      <div
        role="group"
        aria-label={`Availability for ${item.name.trim() || "item"}`}
        className="flex flex-wrap gap-1 mt-3"
      >
        {AVAILABILITY_OPTIONS.map((option) => {
          const selected = item.availability === option.value;
          return (
            <button
              key={option.value}
              type="button"
              aria-pressed={selected}
              onClick={() => onSetAvailability(option.value)}
              className={`inline-flex items-center gap-1 rounded px-3 py-1.5 text-body-sm font-bold border transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${
                selected
                  ? "bg-primary text-on-primary border-primary"
                  : "bg-surface-container-lowest text-on-surface border-outline-variant hover:bg-surface-container-high"
              }`}
            >
              {selected ? <Icon name="check" className="text-[16px]" /> : null}
              {option.label}
            </button>
          );
        })}
      </div>

      {/* Row actions */}
      <div className="flex flex-wrap items-center gap-component-gap-sm mt-3">
        <Button
          size="sm"
          variant="secondary"
          aria-label={`Move ${item.name.trim() || "item"} up`}
          disabled={index === 0}
          onClick={onMoveUp}
        >
          <Icon name="arrow_upward" className="text-[16px]" />
        </Button>
        <Button
          size="sm"
          variant="secondary"
          aria-label={`Move ${item.name.trim() || "item"} down`}
          disabled={index === count - 1}
          onClick={onMoveDown}
        >
          <Icon name="arrow_downward" className="text-[16px]" />
        </Button>

        {otherStations.length > 0 ? (
          <div>
            <label htmlFor={moveId} className="sr-only">
              Move {item.name.trim() || "item"} to another station
            </label>
            <select
              id={moveId}
              className="rounded border border-outline-variant bg-surface-container-lowest px-2 py-1.5 text-body-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              value=""
              onChange={(e) => {
                if (e.target.value) onMoveToStation(e.target.value);
              }}
            >
              <option value="">Move to…</option>
              {otherStations.map((station) => (
                <option key={station.id} value={station.id}>
                  {station.name}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        <Button
          size="sm"
          variant="secondary"
          icon={editing ? "expand_less" : "edit"}
          aria-expanded={editing}
          onClick={() => setEditing((prev) => !prev)}
        >
          {editing ? "Close" : "Edit"}
        </Button>
        <Button
          size="sm"
          variant="ghost"
          icon="delete"
          aria-label={`Remove ${item.name.trim() || "item"}`}
          onClick={onRemove}
        >
          Remove
        </Button>
      </div>

      {/* Edit details */}
      {editing ? (
        <div className="mt-3 pt-3 border-t border-outline-variant space-y-4">
          <div>
            <label
              htmlFor={nameId}
              className="block text-label-md text-secondary uppercase mb-1"
            >
              Display name
            </label>
            <input
              id={nameId}
              type="text"
              className={fieldClass}
              value={item.name}
              aria-invalid={nameInvalid}
              onChange={(e) => onUpdate({ name: e.target.value })}
            />
            {nameInvalid ? (
              <p className="text-body-sm text-error mt-1">
                A display name is required to publish.
              </p>
            ) : null}
          </div>

          <div>
            <label
              htmlFor={`${nameId}-category`}
              className="block text-label-md text-secondary uppercase mb-1"
            >
              Category
            </label>
            <select
              id={`${nameId}-category`}
              className={fieldClass}
              value={item.category}
              onChange={(e) =>
                onUpdate({ category: e.target.value as FoodCategory })
              }
            >
              {FOOD_CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>

          <fieldset>
            <legend className="text-label-md text-secondary uppercase mb-1">
              Dietary tags
            </legend>
            <div className="flex flex-wrap gap-3">
              {DIETARY_TAGS.map((tag) => (
                <label
                  key={tag}
                  className="flex items-center gap-2 text-body-sm"
                >
                  <input
                    type="checkbox"
                    checked={item.dietaryTags.includes(tag)}
                    onChange={() =>
                      onUpdate({
                        dietaryTags: toggle<DietaryTag>(item.dietaryTags, tag),
                      })
                    }
                  />
                  {tag}
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend className="text-label-md text-secondary uppercase mb-1">
              Allergen labels
            </legend>
            <div className="flex flex-wrap gap-3">
              {ALLERGENS.map((allergen) => (
                <label
                  key={allergen}
                  className="flex items-center gap-2 text-body-sm"
                >
                  <input
                    type="checkbox"
                    checked={item.allergens.includes(allergen)}
                    onChange={() =>
                      onUpdate({
                        allergens: toggle<Allergen>(item.allergens, allergen),
                      })
                    }
                  />
                  {allergen}
                </label>
              ))}
            </div>
          </fieldset>

          <div>
            <label
              htmlFor={noteId}
              className="block text-label-md text-secondary uppercase mb-1"
            >
              Student-facing note
            </label>
            <input
              id={noteId}
              type="text"
              className={fieldClass}
              value={item.studentNote ?? ""}
              placeholder="Optional note shown to students"
              onChange={(e) => onUpdate({ studentNote: e.target.value })}
            />
          </div>
        </div>
      ) : null}
    </li>
  );
}
