import {
  DAYS_OF_WEEK,
  type DayHours,
  type DayOfWeek,
  type WeeklyHours,
} from "../../data/locationTypes";

interface LocationHoursEditorProps {
  hours: WeeklyHours;
  onChange: (day: DayOfWeek, patch: Partial<DayHours>) => void;
}

const timeClass =
  "rounded border border-outline-variant bg-surface-container-lowest px-2 py-1.5 text-body-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50";

export function LocationHoursEditor({
  hours,
  onChange,
}: LocationHoursEditorProps) {
  return (
    <fieldset className="space-y-2">
      <legend className="font-h3 text-h3 mb-2">Operating hours</legend>
      <ul className="space-y-2">
        {DAYS_OF_WEEK.map(({ value, label }) => {
          const day = hours[value];
          const invalid =
            !day.closed && !!day.open && !!day.close && day.close <= day.open;
          return (
            <li
              key={value}
              className="flex flex-wrap items-center gap-component-gap-md border border-outline-variant rounded p-2"
            >
              <span className="w-24 font-body-md font-bold">{label}</span>
              <label className="flex items-center gap-2 text-body-sm">
                <input
                  type="checkbox"
                  checked={!day.closed}
                  onChange={(e) =>
                    onChange(value, { closed: !e.target.checked })
                  }
                />
                Open
              </label>
              <label className="flex items-center gap-1 text-body-sm">
                <span className="sr-only">{label} opening time</span>
                <input
                  type="time"
                  className={timeClass}
                  value={day.open}
                  disabled={day.closed}
                  aria-label={`${label} opening time`}
                  onChange={(e) => onChange(value, { open: e.target.value })}
                />
              </label>
              <span aria-hidden="true">–</span>
              <label className="flex items-center gap-1 text-body-sm">
                <span className="sr-only">{label} closing time</span>
                <input
                  type="time"
                  className={timeClass}
                  value={day.close}
                  disabled={day.closed}
                  aria-label={`${label} closing time`}
                  aria-invalid={invalid}
                  onChange={(e) => onChange(value, { close: e.target.value })}
                />
              </label>
              {invalid ? (
                <span className="text-body-sm text-error">
                  Closing must be after opening.
                </span>
              ) : null}
            </li>
          );
        })}
      </ul>
    </fieldset>
  );
}
