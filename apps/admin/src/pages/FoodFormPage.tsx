import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { FoodForm } from "../components/foods/FoodForm";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Icon } from "../components/ui/Icon";
import { LiveRegion } from "../components/ui/LiveRegion";
import { StatusBadge } from "../components/ui/StatusBadge";
import { ValidationSummary } from "../components/ui/ValidationSummary";
import {
  foodStatusLabel,
  foodStatusTone,
  type FoodCatalogItem,
} from "../data/foodTypes";
import { buildFood } from "../state/foodOps";
import { useFoodCatalog } from "../state/FoodCatalogProvider";
import {
  validateFoodForActivation,
  type ValidationIssue,
} from "../state/foodValidation";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";

export function FoodFormPage() {
  const { foodId } = useParams();
  const navigate = useNavigate();
  const store = useFoodCatalog();
  const isCreate = !foodId;

  const [draft, setDraft] = useState<FoodCatalogItem>(() => buildFood());
  const [dirty, setDirty] = useState(false);
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [leaveOpen, setLeaveOpen] = useState(false);
  const [message, setMessage] = useState("");

  const existing = foodId ? store.getFood(foodId) : undefined;

  if (!isCreate && !existing) {
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

  const food = isCreate ? draft : (existing as FoodCatalogItem);

  const update = (fn: (f: FoodCatalogItem) => FoodCatalogItem) => {
    if (isCreate) setDraft((d) => fn(d));
    else store.updateWith(food.id, fn);
    setDirty(true);
    setIssues([]);
  };

  const commitCreate = (status: FoodCatalogItem["status"]) => {
    store.create({
      ...draft,
      status,
      updatedAt: "Just now",
      updatedBy: "John Doe",
    });
    navigate("/foods");
  };

  const saveDraft = () => {
    if (isCreate) {
      commitCreate("draft");
      return;
    }
    store.setStatus(food.id, "draft");
    setDirty(false);
    setIssues([]);
    setMessage("Draft updated for this session.");
  };

  const activate = () => {
    const found = validateFoodForActivation(food);
    if (found.length > 0) {
      setIssues(found);
      setMessage(
        `Cannot activate — resolve ${found.length} issue${
          found.length === 1 ? "" : "s"
        } below.`,
      );
      return;
    }
    if (isCreate) {
      commitCreate("active");
      return;
    }
    store.setStatus(food.id, "active");
    setDirty(false);
    setIssues([]);
    setMessage("Food item activated for this session.");
  };

  const goBack = () => {
    if (dirty) setLeaveOpen(true);
    else navigate("/foods");
  };

  return (
    <div className="p-container-padding space-y-gutter max-w-7xl mx-auto">
      <LiveRegion message={message} />

      <div className="space-y-3">
        <button
          type="button"
          onClick={goBack}
          className="inline-flex items-center gap-1 text-primary font-bold text-body-sm rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <Icon name="arrow_back" className="text-[18px]" />
          Back to food catalog
        </button>

        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="font-h2 text-h2">
              {isCreate ? "New food item" : food.name.trim() || "Untitled item"}
            </h2>
            <StatusBadge tone={foodStatusTone[food.status]}>
              {foodStatusLabel(food.status)}
            </StatusBadge>
            {dirty ? (
              <span className="inline-flex items-center gap-1 text-body-sm text-yellow-600 font-bold">
                <Icon name="edit_note" className="text-[18px]" />
                Unsaved changes
              </span>
            ) : null}
          </div>

          <div className="flex flex-wrap gap-component-gap-sm">
            {!isCreate ? (
              <Button
                variant="secondary"
                icon="visibility"
                onClick={() => navigate(`/foods/${food.id}/preview`)}
              >
                Preview
              </Button>
            ) : null}
            <Button variant="secondary" icon="save" onClick={saveDraft}>
              Save Draft
            </Button>
            <Button variant="primary" icon="check_circle" onClick={activate}>
              Activate
            </Button>
          </div>
        </div>
      </div>

      <ValidationSummary issues={issues} />

      <FoodForm food={food} update={update} />

      <ConfirmDialog
        open={leaveOpen}
        title="Discard unsaved changes?"
        message="You have unsaved changes for this session. Leaving will return you to the food catalog."
        confirmLabel="Leave"
        cancelLabel="Stay"
        onConfirm={() => {
          setLeaveOpen(false);
          navigate("/foods");
        }}
        onCancel={() => setLeaveOpen(false)}
      />
    </div>
  );
}
