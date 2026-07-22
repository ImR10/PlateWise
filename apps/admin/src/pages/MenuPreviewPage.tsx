import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { MenuNotFound } from "../components/menus/MenuNotFound";
import { MenuPreview } from "../components/menus/MenuPreview";
import { Button } from "../components/ui/Button";
import { Icon } from "../components/ui/Icon";
import {
  mealPeriodLabel,
  menuStatusLabel,
  menuStatusTone,
} from "../data/menuTypes";
import { formatShortDate } from "../lib/dates";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useDiningLocations } from "../state/DiningLocationsProvider";
import { useMenus } from "../state/MenusProvider";

export function MenuPreviewPage() {
  const { menuId } = useParams();
  const navigate = useNavigate();
  const { getMenu } = useMenus();
  const { getLocationName } = useDiningLocations();
  const menu = menuId ? getMenu(menuId) : undefined;

  const [mode, setMode] = useState<"desktop" | "mobile">("desktop");
  const [showUnavailable, setShowUnavailable] = useState(false);

  if (!menu) return <MenuNotFound />;

  return (
    <div className="p-container-padding space-y-gutter max-w-7xl mx-auto">
      <div className="flex flex-wrap items-center gap-4">
        <button
          type="button"
          onClick={() => navigate(`/menus/${menu.id}/edit`)}
          className="inline-flex items-center gap-1 text-primary font-bold text-body-sm rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <Icon name="arrow_back" className="text-[18px]" />
          Back to editor
        </button>
        <button
          type="button"
          onClick={() => navigate("/menus")}
          className="inline-flex items-center gap-1 text-secondary font-bold text-body-sm rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <Icon name="list" className="text-[18px]" />
          Back to menus
        </button>
      </div>

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
        </div>

        <div className="flex flex-wrap items-center gap-component-gap-md">
          <div role="group" aria-label="Preview device" className="flex gap-1">
            <Button
              size="sm"
              variant={mode === "desktop" ? "primary" : "secondary"}
              icon="desktop_windows"
              aria-pressed={mode === "desktop"}
              onClick={() => setMode("desktop")}
            >
              Desktop Preview
            </Button>
            <Button
              size="sm"
              variant={mode === "mobile" ? "primary" : "secondary"}
              icon="smartphone"
              aria-pressed={mode === "mobile"}
              onClick={() => setMode("mobile")}
            >
              Mobile Preview
            </Button>
          </div>
          <label className="flex items-center gap-2 text-body-sm">
            <input
              type="checkbox"
              checked={showUnavailable}
              onChange={(e) => setShowUnavailable(e.target.checked)}
            />
            Show unavailable items
          </label>
        </div>
      </div>

      <p
        role="note"
        className="flex items-center gap-2 admin-card p-3 text-body-sm text-secondary"
      >
        <Icon name="info" className="text-[18px] text-primary" />
        Preview only — changes are stored locally for this session.
      </p>

      <MenuPreview menu={menu} mode={mode} showUnavailable={showUnavailable} />
    </div>
  );
}
