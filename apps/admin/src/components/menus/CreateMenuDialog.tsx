import { useEffect, useState } from "react";

import { diningLocations } from "../../data/locations";
import { MEAL_PERIODS, type MealPeriod } from "../../data/menuTypes";
import type { CreateMenuInput } from "../../state/menuOps";
import { Button } from "../ui/Button";
import { Dialog } from "../ui/Dialog";

interface CreateMenuDialogProps {
  open: boolean;
  defaultDate: string;
  onClose: () => void;
  onCreate: (input: CreateMenuInput) => void;
}

const fieldClass =
  "w-full rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary";
const labelClass = "block text-label-md text-secondary uppercase mb-1";

export function CreateMenuDialog({
  open,
  defaultDate,
  onClose,
  onCreate,
}: CreateMenuDialogProps) {
  const [locationId, setLocationId] = useState("");
  const [date, setDate] = useState(defaultDate);
  const [mealPeriod, setMealPeriod] = useState<MealPeriod>("breakfast");
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");

  // Reset the form each time the dialog is (re)opened.
  useEffect(() => {
    if (open) {
      setLocationId("");
      setDate(defaultDate);
      setMealPeriod("breakfast");
      setTitle("");
      setError("");
    }
  }, [open, defaultDate]);

  const submit = () => {
    if (!locationId) {
      setError("Select a dining location to continue.");
      return;
    }
    onCreate({ locationId, date, mealPeriod, title });
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Create menu"
      description="Start a new menu for a dining location, date, and meal period."
      size="sm"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" icon="add" onClick={submit}>
            Create Menu
          </Button>
        </>
      }
    >
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <div>
          <label htmlFor="create-location" className={labelClass}>
            Dining location
          </label>
          <select
            id="create-location"
            className={fieldClass}
            value={locationId}
            onChange={(e) => setLocationId(e.target.value)}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? "create-location-error" : undefined}
          >
            <option value="">Select a location</option>
            {diningLocations.map((loc) => (
              <option key={loc.id} value={loc.id}>
                {loc.name}
              </option>
            ))}
          </select>
          {error ? (
            <p
              id="create-location-error"
              className="text-body-sm text-error mt-1"
            >
              {error}
            </p>
          ) : null}
        </div>

        <div>
          <label htmlFor="create-date" className={labelClass}>
            Date
          </label>
          <input
            id="create-date"
            type="date"
            className={fieldClass}
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>

        <div>
          <label htmlFor="create-meal" className={labelClass}>
            Meal period
          </label>
          <select
            id="create-meal"
            className={fieldClass}
            value={mealPeriod}
            onChange={(e) => setMealPeriod(e.target.value as MealPeriod)}
          >
            {MEAL_PERIODS.map((meal) => (
              <option key={meal.value} value={meal.value}>
                {meal.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="create-title" className={labelClass}>
            Internal menu title
          </label>
          <input
            id="create-title"
            type="text"
            className={fieldClass}
            value={title}
            placeholder="e.g. Morning service"
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
      </form>
    </Dialog>
  );
}
