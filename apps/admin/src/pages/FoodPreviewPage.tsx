import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { FoodPreview } from "../components/foods/FoodPreview";
import { EmptyState } from "../components/ui/EmptyState";
import { Icon } from "../components/ui/Icon";
import {
  PreviewDeviceToggle,
  PreviewNotice,
  type PreviewMode,
} from "../components/ui/PreviewControls";
import { StatusBadge } from "../components/ui/StatusBadge";
import { foodStatusLabel, foodStatusTone } from "../data/foodTypes";
import { useFoodCatalog } from "../state/FoodCatalogProvider";

export function FoodPreviewPage() {
  const { foodId } = useParams();
  const navigate = useNavigate();
  const { getFood } = useFoodCatalog();
  const food = foodId ? getFood(foodId) : undefined;
  const [mode, setMode] = useState<PreviewMode>("desktop");

  if (!food) {
    return (
      <div className="p-container-padding max-w-7xl mx-auto">
        <EmptyState
          icon="error"
          title="Food item not found"
          message="We couldn't find a food item with that ID. It may have been deleted this session, or the link is invalid."
          action={
            <Link
              to="/foods"
              className="inline-flex items-center gap-1 text-primary font-bold rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              <Icon name="arrow_back" className="text-[18px]" />
              Back to food catalog
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="p-container-padding space-y-gutter max-w-7xl mx-auto">
      <div className="flex flex-wrap items-center gap-4">
        <button
          type="button"
          onClick={() => navigate(`/foods/${food.id}/edit`)}
          className="inline-flex items-center gap-1 text-primary font-bold text-body-sm rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <Icon name="arrow_back" className="text-[18px]" />
          Back to editor
        </button>
        <button
          type="button"
          onClick={() => navigate("/foods")}
          className="inline-flex items-center gap-1 text-secondary font-bold text-body-sm rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <Icon name="list" className="text-[18px]" />
          Back to food catalog
        </button>
      </div>

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="font-h2 text-h2">
            {food.name.trim() || "Untitled item"}
          </h2>
          <StatusBadge tone={foodStatusTone[food.status]}>
            {foodStatusLabel(food.status)}
          </StatusBadge>
        </div>
        <PreviewDeviceToggle mode={mode} onChange={setMode} />
      </div>

      <PreviewNotice />

      <FoodPreview food={food} mode={mode} />
    </div>
  );
}
