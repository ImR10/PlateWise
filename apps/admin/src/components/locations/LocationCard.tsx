import {
  dayLabel,
  locationStatusLabel,
  locationStatusTone,
  type DayOfWeek,
  type DiningLocation,
} from "../../data/locationTypes";
import { mealPeriodLabel } from "../../data/menuTypes";
import { TODAY_ISO, isoWeekdayKey } from "../../lib/dates";
import { Button } from "../ui/Button";
import { Icon } from "../ui/Icon";
import { StatusBadge } from "../ui/StatusBadge";

interface LocationCardProps {
  location: DiningLocation;
  onEdit: (l: DiningLocation) => void;
  onPreview: (l: DiningLocation) => void;
  onDuplicate: (l: DiningLocation) => void;
  onActivate: (l: DiningLocation) => void;
  onMoveDraft: (l: DiningLocation) => void;
  onArchive: (l: DiningLocation) => void;
  onRestore: (l: DiningLocation) => void;
  onDelete: (l: DiningLocation) => void;
}

export function LocationCard({
  location,
  onEdit,
  onPreview,
  onDuplicate,
  onActivate,
  onMoveDraft,
  onArchive,
  onRestore,
  onDelete,
}: LocationCardProps) {
  const name = location.name.trim() || "Untitled location";
  const activeStations = location.stations.filter((s) => s.active).length;
  const todayKey = isoWeekdayKey(TODAY_ISO) as DayOfWeek;
  const today = location.hours[todayKey];
  const todaySummary = today.closed
    ? "Closed today"
    : `${dayLabel(todayKey)}: ${today.open}–${today.close}`;

  return (
    <div className="admin-card p-gutter flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-h3 text-h3">{name}</h3>
          {location.description ? (
            <p className="text-body-sm text-secondary">
              {location.description}
            </p>
          ) : null}
        </div>
        <StatusBadge tone={locationStatusTone[location.status]}>
          {locationStatusLabel(location.status)}
        </StatusBadge>
      </div>

      <dl className="flex flex-wrap gap-x-6 gap-y-1 text-body-sm text-secondary">
        <div className="flex items-center gap-1">
          <dt className="sr-only">Meal periods</dt>
          <Icon name="restaurant_menu" className="text-[16px]" />
          <dd>
            {location.mealPeriods.length > 0
              ? location.mealPeriods.map(mealPeriodLabel).join(", ")
              : "No meal periods"}
          </dd>
        </div>
        <div className="flex items-center gap-1">
          <dt className="sr-only">Active stations</dt>
          <Icon name="grid_view" className="text-[16px]" />
          <dd>
            {activeStations} active station{activeStations === 1 ? "" : "s"}
          </dd>
        </div>
        <div className="flex items-center gap-1">
          <dt className="sr-only">Today's hours</dt>
          <Icon name="schedule" className="text-[16px]" />
          <dd>{todaySummary}</dd>
        </div>
        <div className="flex items-center gap-1">
          <dt className="sr-only">Student visibility</dt>
          <Icon
            name={location.studentVisible ? "visibility" : "visibility_off"}
            className="text-[16px]"
          />
          <dd>{location.studentVisible ? "Visible to students" : "Hidden"}</dd>
        </div>
        <div className="flex items-center gap-1">
          <dt className="sr-only">Last edited</dt>
          <Icon name="history" className="text-[16px]" />
          <dd>
            {location.updatedAt} · {location.updatedBy}
          </dd>
        </div>
      </dl>

      <div className="flex flex-wrap gap-component-gap-sm pt-1">
        <Button
          size="sm"
          variant="secondary"
          icon="visibility"
          aria-label={`Preview ${name}`}
          onClick={() => onPreview(location)}
        >
          Preview
        </Button>
        <Button
          size="sm"
          variant="primary"
          icon="edit"
          aria-label={`Edit ${name}`}
          onClick={() => onEdit(location)}
        >
          Edit
        </Button>
        <Button
          size="sm"
          variant="secondary"
          icon="content_copy"
          aria-label={`Duplicate ${name}`}
          onClick={() => onDuplicate(location)}
        >
          Duplicate
        </Button>
        {location.status !== "active" && location.status !== "archived" ? (
          <Button
            size="sm"
            variant="secondary"
            icon="check_circle"
            aria-label={`Activate ${name}`}
            onClick={() => onActivate(location)}
          >
            Activate
          </Button>
        ) : null}
        {location.status === "active" || location.status === "inactive" ? (
          <Button
            size="sm"
            variant="secondary"
            icon="draft"
            aria-label={`Move ${name} to draft`}
            onClick={() => onMoveDraft(location)}
          >
            Move to Draft
          </Button>
        ) : null}
        {location.status !== "archived" ? (
          <Button
            size="sm"
            variant="secondary"
            icon="archive"
            aria-label={`Archive ${name}`}
            onClick={() => onArchive(location)}
          >
            Archive
          </Button>
        ) : (
          <Button
            size="sm"
            variant="secondary"
            icon="unarchive"
            aria-label={`Restore ${name}`}
            onClick={() => onRestore(location)}
          >
            Restore
          </Button>
        )}
        {location.status === "draft" || location.status === "archived" ? (
          <Button
            size="sm"
            variant="ghost"
            icon="delete"
            aria-label={`Delete ${name}`}
            onClick={() => onDelete(location)}
          >
            Delete
          </Button>
        ) : null}
      </div>
    </div>
  );
}
