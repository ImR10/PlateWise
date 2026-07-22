import { diningLocationName } from "../../data/locations";
import {
  mealPeriodLabel,
  menuStatusLabel,
  menuStatusTone,
  type Menu,
} from "../../data/menuTypes";
import { formatShortDate } from "../../lib/dates";
import { validateMenuForPublish } from "../../state/menuValidation";
import { Button } from "../ui/Button";
import { Icon } from "../ui/Icon";
import { StatusBadge } from "../ui/StatusBadge";

interface MenuCardProps {
  menu: Menu;
  onPreview: (menu: Menu) => void;
  onEdit: (menu: Menu) => void;
  onDuplicate: (menu: Menu) => void;
  onMarkDraft: (menu: Menu) => void;
  onPublish: (menu: Menu) => void;
  onDelete: (menu: Menu) => void;
}

export function MenuCard({
  menu,
  onPreview,
  onEdit,
  onDuplicate,
  onMarkDraft,
  onPublish,
  onDelete,
}: MenuCardProps) {
  const locationName = diningLocationName(menu.locationId);
  const mealLabel = mealPeriodLabel(menu.mealPeriod);
  const descriptor = `${locationName} ${mealLabel}`;
  const stationCount = menu.stations.length;
  const itemCount = menu.stations.reduce((n, s) => n + s.items.length, 0);
  const issues = validateMenuForPublish(menu);

  return (
    <div className="admin-card p-gutter flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-h3 text-h3">{locationName}</h3>
          <p className="text-body-sm text-secondary">
            {mealLabel} • {formatShortDate(menu.date)}
          </p>
        </div>
        <StatusBadge tone={menuStatusTone[menu.status]}>
          {menuStatusLabel(menu.status)}
        </StatusBadge>
      </div>

      <dl className="flex flex-wrap gap-x-6 gap-y-1 text-body-sm text-secondary">
        <div className="flex items-center gap-1">
          <dt className="sr-only">Stations</dt>
          <Icon name="grid_view" className="text-[16px]" />
          <dd>
            {stationCount} station{stationCount === 1 ? "" : "s"}
          </dd>
        </div>
        <div className="flex items-center gap-1">
          <dt className="sr-only">Items</dt>
          <Icon name="restaurant" className="text-[16px]" />
          <dd>
            {itemCount} item{itemCount === 1 ? "" : "s"}
          </dd>
        </div>
        <div className="flex items-center gap-1">
          <dt className="sr-only">Last updated</dt>
          <Icon name="schedule" className="text-[16px]" />
          <dd>
            {menu.updatedAt} · {menu.updatedBy}
          </dd>
        </div>
      </dl>

      {issues.length > 0 ? (
        <p className="flex items-center gap-1 text-body-sm text-on-error-container">
          <Icon name="warning" className="text-[16px] text-yellow-600" />
          {issues.length} issue{issues.length === 1 ? "" : "s"} to resolve
          before publishing
        </p>
      ) : null}

      <div className="flex flex-wrap gap-component-gap-sm pt-1">
        <Button
          size="sm"
          variant="secondary"
          icon="visibility"
          aria-label={`Preview ${descriptor} menu`}
          onClick={() => onPreview(menu)}
        >
          Preview
        </Button>
        <Button
          size="sm"
          variant="primary"
          icon="edit"
          aria-label={`Edit ${descriptor} menu`}
          onClick={() => onEdit(menu)}
        >
          Edit
        </Button>
        <Button
          size="sm"
          variant="secondary"
          icon="content_copy"
          aria-label={`Duplicate ${descriptor} menu`}
          onClick={() => onDuplicate(menu)}
        >
          Duplicate
        </Button>
        <Button
          size="sm"
          variant="secondary"
          icon="draft"
          disabled={menu.status === "draft"}
          aria-label={`Mark ${descriptor} menu as draft`}
          onClick={() => onMarkDraft(menu)}
        >
          Mark as Draft
        </Button>
        <Button
          size="sm"
          variant="secondary"
          icon="publish"
          disabled={menu.status === "published"}
          aria-label={`Publish ${descriptor} menu`}
          onClick={() => onPublish(menu)}
        >
          Publish
        </Button>
        <Button
          size="sm"
          variant="ghost"
          icon="delete"
          aria-label={`Delete ${descriptor} menu`}
          onClick={() => onDelete(menu)}
        >
          Delete
        </Button>
      </div>
    </div>
  );
}
