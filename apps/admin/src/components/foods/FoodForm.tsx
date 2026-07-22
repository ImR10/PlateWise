import {
  FOOD_STATUSES,
  type FoodCatalogItem,
  type FoodStatus,
} from "../../data/foodTypes";
import {
  ALLERGENS,
  AVAILABILITY_OPTIONS,
  DIETARY_TAGS,
  FOOD_CATEGORIES,
  type AvailabilityStatus,
  type FoodCategory,
} from "../../data/menuTypes";
import * as ops from "../../state/foodOps";
import { Button } from "../ui/Button";

const fieldClass =
  "w-full rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary";
const labelClass = "block text-label-md text-secondary uppercase mb-1";

interface FoodFormProps {
  food: FoodCatalogItem;
  update: (fn: (f: FoodCatalogItem) => FoodCatalogItem) => void;
}

export function FoodForm({ food, update }: FoodFormProps) {
  const nameInvalid = !food.name.trim();

  return (
    <div className="space-y-gutter">
      {/* Basic details */}
      <section className="admin-card p-gutter" aria-labelledby="food-basic">
        <h3 id="food-basic" className="font-h3 text-h3 mb-4">
          Basic details
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-component-gap-md">
          <div className="md:col-span-2">
            <label htmlFor="food-name" className={labelClass}>
              Food-item name
            </label>
            <input
              id="food-name"
              type="text"
              className={fieldClass}
              value={food.name}
              aria-invalid={nameInvalid}
              onChange={(e) => update((f) => ({ ...f, name: e.target.value }))}
            />
          </div>
          <div>
            <label htmlFor="food-category-field" className={labelClass}>
              Category
            </label>
            <select
              id="food-category-field"
              className={fieldClass}
              value={food.category}
              onChange={(e) =>
                update((f) => ({
                  ...f,
                  category: e.target.value as FoodCategory,
                }))
              }
            >
              {FOOD_CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="food-status-field" className={labelClass}>
              Status
            </label>
            <select
              id="food-status-field"
              className={fieldClass}
              value={food.status}
              onChange={(e) =>
                update((f) => ({ ...f, status: e.target.value as FoodStatus }))
              }
            >
              {FOOD_STATUSES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <label htmlFor="food-desc" className={labelClass}>
              Short description (optional)
            </label>
            <input
              id="food-desc"
              type="text"
              className={fieldClass}
              value={food.description ?? ""}
              onChange={(e) =>
                update((f) => ({ ...f, description: e.target.value }))
              }
            />
          </div>
          <div className="md:col-span-2">
            <label htmlFor="food-long" className={labelClass}>
              Longer description (optional, student-facing)
            </label>
            <textarea
              id="food-long"
              rows={2}
              className={fieldClass}
              value={food.longDescription ?? ""}
              onChange={(e) =>
                update((f) => ({ ...f, longDescription: e.target.value }))
              }
            />
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 text-body-md">
              <input
                type="checkbox"
                checked={food.studentVisible}
                onChange={(e) =>
                  update((f) => ({ ...f, studentVisible: e.target.checked }))
                }
              />
              Visible to students
            </label>
          </div>
          <div className="md:col-span-2">
            <label htmlFor="food-notes" className={labelClass}>
              Internal notes (admin-only, not student-facing)
            </label>
            <textarea
              id="food-notes"
              rows={2}
              className={fieldClass}
              value={food.internalNotes ?? ""}
              placeholder="Only visible to staff — never shown to students."
              onChange={(e) =>
                update((f) => ({ ...f, internalNotes: e.target.value }))
              }
            />
          </div>
        </div>
      </section>

      {/* Dietary + allergens */}
      <section className="admin-card p-gutter" aria-labelledby="food-diet">
        <h3 id="food-diet" className="font-h3 text-h3 mb-4">
          Dietary information &amp; allergens
        </h3>
        <fieldset className="mb-4">
          <legend className={labelClass}>Dietary tags</legend>
          <div className="flex flex-wrap gap-3">
            {DIETARY_TAGS.map((tag) => (
              <label key={tag} className="flex items-center gap-2 text-body-sm">
                <input
                  type="checkbox"
                  checked={food.dietaryTags.includes(tag)}
                  onChange={() => update((f) => ops.toggleDietaryTag(f, tag))}
                />
                {tag}
              </label>
            ))}
          </div>
        </fieldset>
        <fieldset>
          <div className="flex items-center justify-between mb-1">
            <legend className={labelClass}>Allergens</legend>
            {food.allergens.length > 0 ? (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => update((f) => ops.clearAllergens(f))}
              >
                Clear allergens
              </Button>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-3">
            {ALLERGENS.map((allergen) => (
              <label
                key={allergen}
                className="flex items-center gap-2 text-body-sm"
              >
                <input
                  type="checkbox"
                  checked={food.allergens.includes(allergen)}
                  onChange={() =>
                    update((f) => ops.toggleAllergen(f, allergen))
                  }
                />
                {allergen}
              </label>
            ))}
          </div>
        </fieldset>
      </section>

      {/* Serving metadata */}
      <section className="admin-card p-gutter" aria-labelledby="food-serving">
        <h3 id="food-serving" className="font-h3 text-h3 mb-4">
          Default serving
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-component-gap-md">
          <div>
            <label htmlFor="food-availability" className={labelClass}>
              Default availability
            </label>
            <select
              id="food-availability"
              className={fieldClass}
              value={food.defaultAvailability}
              onChange={(e) =>
                update((f) => ({
                  ...f,
                  defaultAvailability: e.target.value as AvailabilityStatus,
                }))
              }
            >
              {AVAILABILITY_OPTIONS.map((a) => (
                <option key={a.value} value={a.value}>
                  {a.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="food-serving-label" className={labelClass}>
              Serving label (optional)
            </label>
            <input
              id="food-serving-label"
              type="text"
              className={fieldClass}
              value={food.servingLabel ?? ""}
              placeholder="e.g. 1 serving"
              onChange={(e) =>
                update((f) => ({ ...f, servingLabel: e.target.value }))
              }
            />
          </div>
          <div>
            <label htmlFor="food-calories" className={labelClass}>
              Calories estimate (optional)
            </label>
            <input
              id="food-calories"
              type="text"
              className={fieldClass}
              value={food.calories ?? ""}
              placeholder="e.g. 320"
              onChange={(e) =>
                update((f) => ({ ...f, calories: e.target.value }))
              }
            />
          </div>
          <div>
            <label htmlFor="food-portion" className={labelClass}>
              Portion description (optional)
            </label>
            <input
              id="food-portion"
              type="text"
              className={fieldClass}
              value={food.portion ?? ""}
              placeholder="e.g. 1 cup"
              onChange={(e) =>
                update((f) => ({ ...f, portion: e.target.value }))
              }
            />
          </div>
        </div>
      </section>
    </div>
  );
}
