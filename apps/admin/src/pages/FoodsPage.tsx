import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { FoodCard } from "../components/foods/FoodCard";
import {
  FoodFilters,
  emptyFoodFilters,
  foodFiltersActive,
  type FoodFilterState,
} from "../components/foods/FoodFilters";
import { Button } from "../components/ui/Button";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { EmptyState } from "../components/ui/EmptyState";
import { LiveRegion } from "../components/ui/LiveRegion";
import { StatTiles } from "../components/ui/StatTiles";
import type { FoodCatalogItem } from "../data/foodTypes";
import { useFoodCatalog } from "../state/FoodCatalogProvider";
import { validateFoodForActivation } from "../state/foodValidation";

export function FoodsPage() {
  const navigate = useNavigate();
  const { foods, duplicate, remove, setStatus } = useFoodCatalog();
  const [filters, setFilters] = useState<FoodFilterState>(emptyFoodFilters);
  const [pendingDelete, setPendingDelete] = useState<FoodCatalogItem | null>(
    null,
  );
  const [message, setMessage] = useState("");

  const visible = useMemo(() => {
    const term = filters.search.trim().toLowerCase();
    return foods.filter((f) => {
      if (
        f.status === "archived" &&
        !filters.showArchived &&
        filters.status !== "archived"
      )
        return false;
      if (term && !f.name.toLowerCase().includes(term)) return false;
      if (filters.category !== "all" && f.category !== filters.category)
        return false;
      if (filters.dietary !== "all" && !f.dietaryTags.includes(filters.dietary))
        return false;
      if (filters.allergen !== "all" && !f.allergens.includes(filters.allergen))
        return false;
      if (filters.status !== "all" && f.status !== filters.status) return false;
      return true;
    });
  }, [foods, filters]);

  const tiles = [
    { label: "Total Items", value: foods.length, accent: "#5b4040" },
    {
      label: "Active",
      value: foods.filter((f) => f.status === "active").length,
      accent: "#1e7e34",
    },
    {
      label: "Drafts",
      value: foods.filter((f) => f.status === "draft").length,
      accent: "#94a3b8",
    },
    {
      label: "Archived",
      value: foods.filter((f) => f.status === "archived").length,
      accent: "#dc2626",
    },
  ];

  const handleActivate = (f: FoodCatalogItem) => {
    const issues = validateFoodForActivation(f);
    if (issues.length > 0) {
      setMessage(
        `Cannot activate ${f.name || "item"} — resolve ${issues.length} issue${
          issues.length === 1 ? "" : "s"
        } in the editor first.`,
      );
      return;
    }
    setStatus(f.id, "active");
    setMessage(`${f.name} activated for this session.`);
  };

  const confirmDelete = () => {
    if (pendingDelete) {
      remove(pendingDelete.id);
      setMessage("Food item deleted for this session.");
      setPendingDelete(null);
    }
  };

  return (
    <div className="p-container-padding space-y-gutter max-w-7xl mx-auto">
      <LiveRegion message={message} />

      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div>
          <h2 className="font-h2 text-h2">Food Catalog</h2>
          <p className="text-body-sm text-secondary max-w-xl">
            Manage the catalog of food items, dietary tags, and allergens used
            across menus. All data is generic mock data kept in memory for this
            session only.
          </p>
        </div>
        <Button
          variant="primary"
          icon="add_circle"
          onClick={() => navigate("/foods/new")}
        >
          Create Food Item
        </Button>
      </div>

      <StatTiles tiles={tiles} />

      <FoodFilters
        filters={filters}
        onChange={setFilters}
        onClear={() => setFilters(emptyFoodFilters)}
      />

      {foods.length === 0 ? (
        <EmptyState
          icon="no_meals"
          title="No food items yet"
          message="Create your first food item to get started."
          action={
            <Button
              variant="primary"
              icon="add_circle"
              onClick={() => navigate("/foods/new")}
            >
              Create Food Item
            </Button>
          }
        />
      ) : visible.length === 0 ? (
        <EmptyState
          icon="filter_alt"
          title="No food items match your filters"
          message="Try adjusting or clearing the filters to see more items."
          action={
            foodFiltersActive(filters) ? (
              <Button
                variant="secondary"
                icon="filter_alt_off"
                onClick={() => setFilters(emptyFoodFilters)}
              >
                Clear filters
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-gutter">
          {visible.map((food) => (
            <FoodCard
              key={food.id}
              food={food}
              onEdit={(f) => navigate(`/foods/${f.id}/edit`)}
              onPreview={(f) => navigate(`/foods/${f.id}/preview`)}
              onDuplicate={(f) => {
                duplicate(f.id);
                setMessage(`Duplicated ${f.name} for this session.`);
              }}
              onActivate={handleActivate}
              onMoveDraft={(f) => {
                setStatus(f.id, "draft");
                setMessage(`${f.name} moved to draft for this session.`);
              }}
              onArchive={(f) => {
                setStatus(f.id, "archived");
                setMessage(`${f.name} archived for this session.`);
              }}
              onRestore={(f) => {
                setStatus(f.id, "draft");
                setMessage(`${f.name} restored to draft for this session.`);
              }}
              onDelete={(f) => setPendingDelete(f)}
            />
          ))}
        </div>
      )}

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete food item?"
        message={
          pendingDelete
            ? `This permanently removes ${
                pendingDelete.name || "this item"
              } for this session. This cannot be undone.`
            : ""
        }
        confirmLabel="Delete"
        destructive
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
      />
    </div>
  );
}
