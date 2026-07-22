import {
  LOCATION_STATUSES,
  type DiningLocation,
  type LocationStation,
  type LocationStatus,
} from "../../data/locationTypes";
import { MEAL_PERIODS } from "../../data/menuTypes";
import * as ops from "../../state/locationOps";
import { LocationHoursEditor } from "./LocationHoursEditor";
import { LocationStationsEditor } from "./LocationStationsEditor";

const fieldClass =
  "w-full rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary";
const labelClass = "block text-label-md text-secondary uppercase mb-1";

interface LocationFormProps {
  location: DiningLocation;
  update: (fn: (l: DiningLocation) => DiningLocation) => void;
  onRemoveStation: (station: LocationStation) => void;
}

export function LocationForm({
  location,
  update,
  onRemoveStation,
}: LocationFormProps) {
  const nameInvalid = !location.name.trim();

  return (
    <div className="space-y-gutter">
      {/* Basic details */}
      <section className="admin-card p-gutter" aria-labelledby="loc-basic">
        <h3 id="loc-basic" className="font-h3 text-h3 mb-4">
          Basic details
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-component-gap-md">
          <div className="md:col-span-2">
            <label htmlFor="loc-name" className={labelClass}>
              Location name
            </label>
            <input
              id="loc-name"
              type="text"
              className={fieldClass}
              value={location.name}
              aria-invalid={nameInvalid}
              onChange={(e) => update((l) => ({ ...l, name: e.target.value }))}
            />
          </div>
          <div className="md:col-span-2">
            <label htmlFor="loc-desc" className={labelClass}>
              Short description (student-facing)
            </label>
            <input
              id="loc-desc"
              type="text"
              className={fieldClass}
              value={location.description}
              onChange={(e) =>
                update((l) => ({ ...l, description: e.target.value }))
              }
            />
          </div>
          <div className="md:col-span-2">
            <label htmlFor="loc-long" className={labelClass}>
              Longer description (optional, student-facing)
            </label>
            <textarea
              id="loc-long"
              rows={2}
              className={fieldClass}
              value={location.longDescription ?? ""}
              onChange={(e) =>
                update((l) => ({ ...l, longDescription: e.target.value }))
              }
            />
          </div>
          <div>
            <label htmlFor="loc-status" className={labelClass}>
              Status
            </label>
            <select
              id="loc-status"
              className={fieldClass}
              value={location.status}
              onChange={(e) =>
                update((l) => ({
                  ...l,
                  status: e.target.value as LocationStatus,
                }))
              }
            >
              {LOCATION_STATUSES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 text-body-md">
              <input
                type="checkbox"
                checked={location.studentVisible}
                onChange={(e) =>
                  update((l) => ({ ...l, studentVisible: e.target.checked }))
                }
              />
              Visible to students
            </label>
          </div>
          <div className="md:col-span-2">
            <label htmlFor="loc-notes" className={labelClass}>
              Internal notes (admin-only, not student-facing)
            </label>
            <textarea
              id="loc-notes"
              rows={2}
              className={fieldClass}
              value={location.internalNotes ?? ""}
              placeholder="Only visible to staff — never shown to students."
              onChange={(e) =>
                update((l) => ({ ...l, internalNotes: e.target.value }))
              }
            />
          </div>
        </div>
      </section>

      {/* Service configuration */}
      <section className="admin-card p-gutter" aria-labelledby="loc-service">
        <h3 id="loc-service" className="font-h3 text-h3 mb-4">
          Service configuration
        </h3>
        <fieldset className="mb-4">
          <legend className={labelClass}>Supported meal periods</legend>
          <div className="flex flex-wrap gap-3">
            {MEAL_PERIODS.map((meal) => (
              <label
                key={meal.value}
                className="flex items-center gap-2 text-body-sm"
              >
                <input
                  type="checkbox"
                  checked={location.mealPeriods.includes(meal.value)}
                  onChange={() =>
                    update((l) => ops.toggleMealPeriod(l, meal.value))
                  }
                />
                {meal.label}
              </label>
            ))}
          </div>
        </fieldset>
        <LocationStationsEditor
          stations={location.stations}
          onAdd={() => update((l) => ops.addStation(l))}
          onRename={(id, name) => update((l) => ops.renameStation(l, id, name))}
          onToggleActive={(id, active) =>
            update((l) => ops.setStationActive(l, id, active))
          }
          onMove={(id, dir) => update((l) => ops.moveStation(l, id, dir))}
          onRemove={onRemoveStation}
        />
      </section>

      {/* Operating hours */}
      <section className="admin-card p-gutter" aria-labelledby="loc-hours">
        <h3 id="loc-hours" className="sr-only">
          Operating hours
        </h3>
        <LocationHoursEditor
          hours={location.hours}
          onChange={(day, patch) =>
            update((l) => ops.updateDayHours(l, day, patch))
          }
        />
      </section>
    </div>
  );
}
