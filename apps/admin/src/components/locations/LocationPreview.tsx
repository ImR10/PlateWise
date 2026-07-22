import { SAMPLE_INSTITUTION } from "../../data/locations";
import { DAYS_OF_WEEK, type DiningLocation } from "../../data/locationTypes";
import { mealPeriodLabel } from "../../data/menuTypes";
import { previewFrameClass, type PreviewMode } from "../ui/PreviewControls";

/**
 * Student-facing rendering of a dining location. Internal notes and inactive
 * stations are intentionally never shown here.
 */
export function LocationPreview({
  location,
  mode,
}: {
  location: DiningLocation;
  mode: PreviewMode;
}) {
  const activeStations = location.stations.filter((s) => s.active);

  return (
    <div
      className={`${previewFrameClass(mode)} bg-surface-container-lowest overflow-hidden`}
    >
      <div className="bg-primary text-on-primary p-gutter">
        <p className="text-label-md uppercase opacity-90">
          {SAMPLE_INSTITUTION}
        </p>
        <h3 className="font-h2 text-h2">
          {location.name.trim() || "Untitled location"}
        </h3>
        {location.description ? (
          <p className="text-body-sm opacity-90">{location.description}</p>
        ) : null}
      </div>

      <div className="p-gutter space-y-6">
        {location.longDescription ? (
          <p className="text-body-md">{location.longDescription}</p>
        ) : null}

        <section aria-label="Meal periods">
          <h4 className="font-h3 text-h3 mb-2">Meal periods</h4>
          {location.mealPeriods.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {location.mealPeriods.map((mp) => (
                <span
                  key={mp}
                  className="text-[11px] font-bold px-2 py-0.5 rounded bg-secondary-container text-on-secondary-container"
                >
                  {mealPeriodLabel(mp)}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-body-sm text-secondary">
              No meal periods listed.
            </p>
          )}
        </section>

        <section aria-label="Stations">
          <h4 className="font-h3 text-h3 mb-2">Stations</h4>
          {activeStations.length > 0 ? (
            <ul className="list-disc pl-6 text-body-md space-y-1">
              {activeStations.map((station) => (
                <li key={station.id}>{station.name}</li>
              ))}
            </ul>
          ) : (
            <p className="text-body-sm text-secondary">No active stations.</p>
          )}
        </section>

        <section aria-label="Operating hours">
          <h4 className="font-h3 text-h3 mb-2">Operating hours</h4>
          <dl className="space-y-1 text-body-md">
            {DAYS_OF_WEEK.map(({ value, label }) => {
              const day = location.hours[value];
              return (
                <div key={value} className="flex justify-between gap-4">
                  <dt className="text-secondary">{label}</dt>
                  <dd>{day.closed ? "Closed" : `${day.open}–${day.close}`}</dd>
                </div>
              );
            })}
          </dl>
        </section>
      </div>
    </div>
  );
}
