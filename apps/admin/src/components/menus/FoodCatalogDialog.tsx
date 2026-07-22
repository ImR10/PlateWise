import { useEffect, useMemo, useState } from "react";

import { foodCatalog } from "../../data/foods";
import {
  ALLERGENS,
  DIETARY_TAGS,
  FOOD_CATEGORIES,
  type Allergen,
  type DietaryTag,
  type FoodCategory,
  type MenuItem,
} from "../../data/menuTypes";
import { menuItemFromCatalog, menuItemFromCustom } from "../../state/menuOps";
import { Button } from "../ui/Button";
import { Dialog } from "../ui/Dialog";

interface StationOption {
  id: string;
  name: string;
}

interface FoodCatalogDialogProps {
  open: boolean;
  stations: StationOption[];
  defaultStationId: string;
  onClose: () => void;
  onAdd: (stationId: string, items: MenuItem[]) => void;
}

const fieldClass =
  "w-full rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary";
const labelClass = "block text-label-md text-secondary uppercase mb-1";

function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value)
    ? list.filter((entry) => entry !== value)
    : [...list, value];
}

export function FoodCatalogDialog({
  open,
  stations,
  defaultStationId,
  onClose,
  onAdd,
}: FoodCatalogDialogProps) {
  const [mode, setMode] = useState<"catalog" | "custom">("catalog");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<FoodCategory | "all">("all");
  const [dietary, setDietary] = useState<DietaryTag | "all">("all");
  const [selected, setSelected] = useState<string[]>([]);
  const [stationId, setStationId] = useState(defaultStationId);

  const [customName, setCustomName] = useState("");
  const [customCategory, setCustomCategory] =
    useState<FoodCategory>("Category A");
  const [customTags, setCustomTags] = useState<DietaryTag[]>([]);
  const [customAllergens, setCustomAllergens] = useState<Allergen[]>([]);
  const [customDescription, setCustomDescription] = useState("");
  const [customError, setCustomError] = useState("");

  useEffect(() => {
    if (open) {
      setMode("catalog");
      setSearch("");
      setCategory("all");
      setDietary("all");
      setSelected([]);
      setStationId(defaultStationId);
      setCustomName("");
      setCustomCategory("Category A");
      setCustomTags([]);
      setCustomAllergens([]);
      setCustomDescription("");
      setCustomError("");
    }
  }, [open, defaultStationId]);

  const results = useMemo(
    () =>
      foodCatalog.filter((item) => {
        if (
          search.trim() &&
          !item.name.toLowerCase().includes(search.trim().toLowerCase())
        )
          return false;
        if (category !== "all" && item.category !== category) return false;
        if (dietary !== "all" && !item.dietaryTags.includes(dietary))
          return false;
        return true;
      }),
    [search, category, dietary],
  );

  const addSelected = () => {
    const items = foodCatalog
      .filter((item) => selected.includes(item.id))
      .map(menuItemFromCatalog);
    if (items.length === 0) return;
    onAdd(stationId, items);
  };

  const addCustom = () => {
    if (!customName.trim()) {
      setCustomError("Enter a name for the custom item.");
      return;
    }
    onAdd(stationId, [
      menuItemFromCustom({
        name: customName,
        category: customCategory,
        dietaryTags: customTags,
        allergens: customAllergens,
        description: customDescription.trim() || undefined,
      }),
    ]);
  };

  const stationField = (
    <div>
      <label htmlFor="catalog-station" className={labelClass}>
        Destination station
      </label>
      <select
        id="catalog-station"
        className={fieldClass}
        value={stationId}
        onChange={(e) => setStationId(e.target.value)}
      >
        {stations.map((station) => (
          <option key={station.id} value={station.id}>
            {station.name}
          </option>
        ))}
      </select>
    </div>
  );

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Add food item"
      description="Add items from the generic catalog, or create a custom item for this session."
      size="lg"
      footer={
        mode === "catalog" ? (
          <>
            <Button variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              icon="add"
              disabled={selected.length === 0}
              onClick={addSelected}
            >
              Add selected{selected.length > 0 ? ` (${selected.length})` : ""}
            </Button>
          </>
        ) : (
          <>
            <Button variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="primary" icon="add" onClick={addCustom}>
              Add custom item
            </Button>
          </>
        )
      }
    >
      {/* Mode switch */}
      <div
        role="tablist"
        aria-label="Add food item mode"
        className="flex gap-1 mb-4"
      >
        <button
          type="button"
          role="tab"
          aria-selected={mode === "catalog"}
          onClick={() => setMode("catalog")}
          className={`px-3 py-1.5 text-body-sm font-bold rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
            mode === "catalog"
              ? "bg-primary-fixed text-primary"
              : "text-secondary hover:bg-surface-container-high"
          }`}
        >
          From catalog
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "custom"}
          onClick={() => setMode("custom")}
          className={`px-3 py-1.5 text-body-sm font-bold rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
            mode === "custom"
              ? "bg-primary-fixed text-primary"
              : "text-secondary hover:bg-surface-container-high"
          }`}
        >
          Custom item
        </button>
      </div>

      {mode === "catalog" ? (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-component-gap-md">
            <div className="sm:col-span-1">
              <label htmlFor="catalog-search" className={labelClass}>
                Search
              </label>
              <div className="flex gap-1">
                <input
                  id="catalog-search"
                  type="search"
                  className={fieldClass}
                  value={search}
                  placeholder="Search items"
                  onChange={(e) => setSearch(e.target.value)}
                />
                {search ? (
                  <Button
                    variant="secondary"
                    aria-label="Clear search"
                    onClick={() => setSearch("")}
                  >
                    Clear
                  </Button>
                ) : null}
              </div>
            </div>
            <div>
              <label htmlFor="catalog-category" className={labelClass}>
                Category
              </label>
              <select
                id="catalog-category"
                className={fieldClass}
                value={category}
                onChange={(e) =>
                  setCategory(e.target.value as FoodCategory | "all")
                }
              >
                <option value="all">All categories</option>
                {FOOD_CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="catalog-dietary" className={labelClass}>
                Dietary tag
              </label>
              <select
                id="catalog-dietary"
                className={fieldClass}
                value={dietary}
                onChange={(e) =>
                  setDietary(e.target.value as DietaryTag | "all")
                }
              >
                <option value="all">All dietary tags</option>
                {DIETARY_TAGS.map((tag) => (
                  <option key={tag} value={tag}>
                    {tag}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {stationField}

          <ul
            className="space-y-2 max-h-72 overflow-y-auto"
            aria-label="Catalog items"
          >
            {results.length === 0 ? (
              <li className="text-body-sm text-secondary py-4 text-center">
                No catalog items match your search.
              </li>
            ) : (
              results.map((item) => (
                <li key={item.id}>
                  <label className="flex items-start gap-3 border border-outline-variant rounded p-3 cursor-pointer hover:bg-surface-container-high">
                    <input
                      type="checkbox"
                      className="mt-1"
                      checked={selected.includes(item.id)}
                      onChange={() => setSelected((s) => toggle(s, item.id))}
                    />
                    <span className="min-w-0">
                      <span className="block font-body-md font-bold">
                        {item.name}
                      </span>
                      <span className="block text-body-sm text-secondary">
                        {item.category}
                        {item.dietaryTags.length > 0
                          ? ` • ${item.dietaryTags.join(", ")}`
                          : ""}
                        {item.allergens.length > 0
                          ? ` • Contains: ${item.allergens.join(", ")}`
                          : ""}
                      </span>
                    </span>
                  </label>
                </li>
              ))
            )}
          </ul>
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <label htmlFor="custom-name" className={labelClass}>
              Name
            </label>
            <input
              id="custom-name"
              type="text"
              className={fieldClass}
              value={customName}
              aria-invalid={Boolean(customError)}
              aria-describedby={customError ? "custom-name-error" : undefined}
              onChange={(e) => setCustomName(e.target.value)}
            />
            {customError ? (
              <p
                id="custom-name-error"
                className="text-body-sm text-error mt-1"
              >
                {customError}
              </p>
            ) : null}
          </div>

          <div>
            <label htmlFor="custom-category" className={labelClass}>
              Category
            </label>
            <select
              id="custom-category"
              className={fieldClass}
              value={customCategory}
              onChange={(e) =>
                setCustomCategory(e.target.value as FoodCategory)
              }
            >
              {FOOD_CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <fieldset>
            <legend className={labelClass}>Dietary tags</legend>
            <div className="flex flex-wrap gap-3">
              {DIETARY_TAGS.map((tag) => (
                <label
                  key={tag}
                  className="flex items-center gap-2 text-body-sm"
                >
                  <input
                    type="checkbox"
                    checked={customTags.includes(tag)}
                    onChange={() => setCustomTags((t) => toggle(t, tag))}
                  />
                  {tag}
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend className={labelClass}>Allergen labels</legend>
            <div className="flex flex-wrap gap-3">
              {ALLERGENS.map((allergen) => (
                <label
                  key={allergen}
                  className="flex items-center gap-2 text-body-sm"
                >
                  <input
                    type="checkbox"
                    checked={customAllergens.includes(allergen)}
                    onChange={() =>
                      setCustomAllergens((a) => toggle(a, allergen))
                    }
                  />
                  {allergen}
                </label>
              ))}
            </div>
          </fieldset>

          <div>
            <label htmlFor="custom-description" className={labelClass}>
              Description
            </label>
            <input
              id="custom-description"
              type="text"
              className={fieldClass}
              value={customDescription}
              placeholder="Optional"
              onChange={(e) => setCustomDescription(e.target.value)}
            />
          </div>

          {stationField}
        </div>
      )}
    </Dialog>
  );
}
