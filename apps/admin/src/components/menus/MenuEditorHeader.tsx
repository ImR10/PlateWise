import {
  mealPeriodLabel,
  menuStatusLabel,
  menuStatusTone,
  type Menu,
} from "../../data/menuTypes";
import { formatShortDate } from "../../lib/dates";
import { useDiningLocations } from "../../state/DiningLocationsProvider";
import { Button } from "../ui/Button";
import { Icon } from "../ui/Icon";
import { StatusBadge } from "../ui/StatusBadge";

interface MenuEditorHeaderProps {
  menu: Menu;
  dirty: boolean;
  onBack: () => void;
  onPreview: () => void;
  onSaveDraft: () => void;
  onPublish: () => void;
}

export function MenuEditorHeader({
  menu,
  dirty,
  onBack,
  onPreview,
  onSaveDraft,
  onPublish,
}: MenuEditorHeaderProps) {
  const { getLocationName } = useDiningLocations();
  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex items-center gap-1 text-primary font-bold text-body-sm rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
      >
        <Icon name="arrow_back" className="text-[18px]" />
        Back to menus
      </button>

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <h2 className="font-h2 text-h2">
              {getLocationName(menu.locationId)}
            </h2>
            <p className="text-body-sm text-secondary">
              {mealPeriodLabel(menu.mealPeriod)} • {formatShortDate(menu.date)}
            </p>
          </div>
          <StatusBadge tone={menuStatusTone[menu.status]}>
            {menuStatusLabel(menu.status)}
          </StatusBadge>
          {dirty ? (
            <span className="inline-flex items-center gap-1 text-body-sm text-yellow-600 font-bold">
              <Icon name="edit_note" className="text-[18px]" />
              Unsaved changes
            </span>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-component-gap-sm">
          <Button variant="secondary" icon="visibility" onClick={onPreview}>
            Preview
          </Button>
          <Button variant="secondary" icon="save" onClick={onSaveDraft}>
            Save Draft
          </Button>
          <Button variant="primary" icon="publish" onClick={onPublish}>
            Publish
          </Button>
        </div>
      </div>
    </div>
  );
}
