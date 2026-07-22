import { SAMPLE_INSTITUTION, diningLocationName } from "../../data/locations";
import {
  availabilityLabel,
  availabilityTone,
  mealPeriodLabel,
  type Menu,
} from "../../data/menuTypes";
import { formatDisplayDate } from "../../lib/dates";
import { StatusBadge } from "../ui/StatusBadge";

interface MenuPreviewProps {
  menu: Menu;
  mode: "desktop" | "mobile";
  showUnavailable: boolean;
}

/**
 * Student-facing rendering of a menu. Internal-only fields (internal title and
 * internal notes) are intentionally never shown here.
 */
export function MenuPreview({ menu, mode, showUnavailable }: MenuPreviewProps) {
  const containerClass =
    mode === "mobile"
      ? "max-w-sm mx-auto border border-outline-variant rounded-xl shadow-sm"
      : "w-full max-w-3xl mx-auto border border-outline-variant rounded-lg";

  return (
    <div
      className={`${containerClass} bg-surface-container-lowest overflow-hidden`}
    >
      <div className="bg-primary text-on-primary p-gutter">
        <p className="text-label-md uppercase opacity-90">
          {SAMPLE_INSTITUTION}
        </p>
        <h3 className="font-h2 text-h2">
          {diningLocationName(menu.locationId)}
        </h3>
        <p className="text-body-sm opacity-90">
          {mealPeriodLabel(menu.mealPeriod)} • {formatDisplayDate(menu.date)}
        </p>
      </div>

      <div className="p-gutter space-y-6">
        {menu.stations.map((station) => {
          const items = station.items.filter(
            (item) => showUnavailable || item.availability !== "unavailable",
          );
          return (
            <section key={station.id} aria-label={station.name}>
              <h4 className="font-h3 text-h3 border-b border-outline-variant pb-1 mb-3">
                {station.name}
              </h4>
              {items.length === 0 ? (
                <p className="text-body-sm text-secondary">
                  No items to show for this station.
                </p>
              ) : (
                <ul className="space-y-3">
                  {items.map((item) => (
                    <li key={item.id}>
                      <div className="flex items-start justify-between gap-2">
                        <p className="font-body-md font-bold">{item.name}</p>
                        <StatusBadge tone={availabilityTone[item.availability]}>
                          {availabilityLabel(item.availability)}
                        </StatusBadge>
                      </div>
                      {item.studentNote ? (
                        <p className="text-body-sm text-secondary">
                          {item.studentNote}
                        </p>
                      ) : null}
                      {item.dietaryTags.length > 0 ||
                      item.allergens.length > 0 ? (
                        <div className="flex flex-wrap gap-1 mt-1">
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
                    </li>
                  ))}
                </ul>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}
