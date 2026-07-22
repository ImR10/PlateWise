import {
  foodStatusLabel,
  foodStatusTone,
  type FoodCatalogItem,
} from "../../data/foodTypes";
import { availabilityLabel } from "../../data/menuTypes";
import { Button } from "../ui/Button";
import { Icon } from "../ui/Icon";
import { StatusBadge } from "../ui/StatusBadge";

interface FoodCardProps {
  food: FoodCatalogItem;
  onEdit: (f: FoodCatalogItem) => void;
  onPreview: (f: FoodCatalogItem) => void;
  onDuplicate: (f: FoodCatalogItem) => void;
  onActivate: (f: FoodCatalogItem) => void;
  onMoveDraft: (f: FoodCatalogItem) => void;
  onArchive: (f: FoodCatalogItem) => void;
  onRestore: (f: FoodCatalogItem) => void;
  onDelete: (f: FoodCatalogItem) => void;
}

export function FoodCard({
  food,
  onEdit,
  onPreview,
  onDuplicate,
  onActivate,
  onMoveDraft,
  onArchive,
  onRestore,
  onDelete,
}: FoodCardProps) {
  const name = food.name.trim() || "Untitled item";

  return (
    <div className="admin-card p-gutter flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-h3 text-h3">{name}</h3>
          <p className="text-body-sm text-secondary">
            {food.category} · {availabilityLabel(food.defaultAvailability)}
          </p>
        </div>
        <StatusBadge tone={foodStatusTone[food.status]}>
          {foodStatusLabel(food.status)}
        </StatusBadge>
      </div>

      {food.description ? (
        <p className="text-body-sm text-secondary">{food.description}</p>
      ) : null}

      {food.dietaryTags.length > 0 || food.allergens.length > 0 ? (
        <div className="flex flex-wrap gap-1">
          {food.dietaryTags.map((tag) => (
            <span
              key={tag}
              className="text-[11px] font-bold px-2 py-0.5 rounded bg-secondary-container text-on-secondary-container"
            >
              {tag}
            </span>
          ))}
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
      ) : null}

      <p className="flex items-center gap-1 text-body-sm text-secondary">
        <Icon
          name={food.studentVisible ? "visibility" : "visibility_off"}
          className="text-[16px]"
        />
        {food.studentVisible ? "Visible to students" : "Hidden from students"}
      </p>

      <div className="flex flex-wrap gap-component-gap-sm pt-1">
        <Button
          size="sm"
          variant="secondary"
          icon="visibility"
          aria-label={`Preview ${name}`}
          onClick={() => onPreview(food)}
        >
          Preview
        </Button>
        <Button
          size="sm"
          variant="primary"
          icon="edit"
          aria-label={`Edit ${name}`}
          onClick={() => onEdit(food)}
        >
          Edit
        </Button>
        <Button
          size="sm"
          variant="secondary"
          icon="content_copy"
          aria-label={`Duplicate ${name}`}
          onClick={() => onDuplicate(food)}
        >
          Duplicate
        </Button>
        {food.status !== "active" && food.status !== "archived" ? (
          <Button
            size="sm"
            variant="secondary"
            icon="check_circle"
            aria-label={`Activate ${name}`}
            onClick={() => onActivate(food)}
          >
            Activate
          </Button>
        ) : null}
        {food.status === "active" ? (
          <Button
            size="sm"
            variant="secondary"
            icon="draft"
            aria-label={`Move ${name} to draft`}
            onClick={() => onMoveDraft(food)}
          >
            Move to Draft
          </Button>
        ) : null}
        {food.status !== "archived" ? (
          <Button
            size="sm"
            variant="secondary"
            icon="archive"
            aria-label={`Archive ${name}`}
            onClick={() => onArchive(food)}
          >
            Archive
          </Button>
        ) : (
          <Button
            size="sm"
            variant="secondary"
            icon="unarchive"
            aria-label={`Restore ${name}`}
            onClick={() => onRestore(food)}
          >
            Restore
          </Button>
        )}
        {food.status === "draft" || food.status === "archived" ? (
          <Button
            size="sm"
            variant="ghost"
            icon="delete"
            aria-label={`Delete ${name}`}
            onClick={() => onDelete(food)}
          >
            Delete
          </Button>
        ) : null}
      </div>
    </div>
  );
}
