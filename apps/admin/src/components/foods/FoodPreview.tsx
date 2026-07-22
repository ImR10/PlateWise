import type { FoodCatalogItem } from "../../data/foodTypes";
import { SAMPLE_INSTITUTION } from "../../data/locations";
import { availabilityLabel } from "../../data/menuTypes";
import { StatusBadge } from "../ui/StatusBadge";
import { availabilityTone } from "../../data/menuTypes";
import { previewFrameClass, type PreviewMode } from "../ui/PreviewControls";

/**
 * Student-facing rendering of a food item. Internal notes are never shown.
 */
export function FoodPreview({
  food,
  mode,
}: {
  food: FoodCatalogItem;
  mode: PreviewMode;
}) {
  return (
    <div
      className={`${previewFrameClass(mode)} bg-surface-container-lowest overflow-hidden`}
    >
      <div className="bg-primary text-on-primary p-gutter">
        <p className="text-label-md uppercase opacity-90">
          {SAMPLE_INSTITUTION}
        </p>
        <h3 className="font-h2 text-h2">
          {food.name.trim() || "Untitled item"}
        </h3>
        <p className="text-body-sm opacity-90">{food.category}</p>
      </div>

      <div className="p-gutter space-y-5">
        <div className="flex items-center gap-2">
          <StatusBadge tone={availabilityTone[food.defaultAvailability]}>
            {availabilityLabel(food.defaultAvailability)}
          </StatusBadge>
          {food.servingLabel ? (
            <span className="text-body-sm text-secondary">
              {food.servingLabel}
            </span>
          ) : null}
        </div>

        {food.description || food.longDescription ? (
          <p className="text-body-md">
            {food.longDescription || food.description}
          </p>
        ) : null}

        <section aria-label="Dietary tags">
          <h4 className="font-h3 text-h3 mb-2">Dietary tags</h4>
          {food.dietaryTags.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {food.dietaryTags.map((tag) => (
                <span
                  key={tag}
                  className="text-[11px] font-bold px-2 py-0.5 rounded bg-secondary-container text-on-secondary-container"
                >
                  {tag}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-body-sm text-secondary">No dietary tags.</p>
          )}
        </section>

        <section aria-label="Allergens">
          <h4 className="font-h3 text-h3 mb-2">Allergens</h4>
          {food.allergens.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {food.allergens.map((allergen) => (
                <span
                  key={allergen}
                  className="text-[11px] font-bold px-2 py-0.5 rounded bg-error-container text-on-error-container"
                >
                  <span className="sr-only">Contains </span>
                  {allergen}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-body-sm text-secondary">
              No allergens listed for this item.
            </p>
          )}
        </section>

        {food.servingLabel || food.calories || food.portion ? (
          <section aria-label="Serving information">
            <h4 className="font-h3 text-h3 mb-2">Serving information</h4>
            <dl className="space-y-1 text-body-md">
              {food.servingLabel ? (
                <div className="flex justify-between gap-4">
                  <dt className="text-secondary">Serving</dt>
                  <dd>{food.servingLabel}</dd>
                </div>
              ) : null}
              {food.calories ? (
                <div className="flex justify-between gap-4">
                  <dt className="text-secondary">Calories</dt>
                  <dd>{food.calories}</dd>
                </div>
              ) : null}
              {food.portion ? (
                <div className="flex justify-between gap-4">
                  <dt className="text-secondary">Portion</dt>
                  <dd>{food.portion}</dd>
                </div>
              ) : null}
            </dl>
          </section>
        ) : null}
      </div>
    </div>
  );
}
