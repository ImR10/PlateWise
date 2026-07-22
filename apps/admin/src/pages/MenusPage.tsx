import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { CreateMenuDialog } from "../components/menus/CreateMenuDialog";
import { MenuCard } from "../components/menus/MenuCard";
import {
  MenuFilters,
  emptyFilters,
  filtersActive,
  type MenuFilterState,
} from "../components/menus/MenuFilters";
import { MenuSummaryCards } from "../components/menus/MenuSummaryCards";
import { Button } from "../components/ui/Button";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { Icon } from "../components/ui/Icon";
import { LiveRegion } from "../components/ui/LiveRegion";
import { mealPeriodLabel, type Menu } from "../data/menuTypes";
import { TODAY_ISO, addDaysIso, formatDisplayDate } from "../lib/dates";
import { useDiningLocations } from "../state/DiningLocationsProvider";
import { useMenus } from "../state/MenusProvider";
import { validateMenuForPublish } from "../state/menuValidation";

export function MenusPage() {
  const navigate = useNavigate();
  const { menus, createMenu, duplicateMenu, deleteMenu, setStatus } =
    useMenus();
  const { getLocationName } = useDiningLocations();

  const [selectedDate, setSelectedDate] = useState(TODAY_ISO);
  const [filters, setFilters] = useState<MenuFilterState>(emptyFilters);
  const [createOpen, setCreateOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Menu | null>(null);
  const [message, setMessage] = useState("");

  const dateMenus = useMemo(
    () => menus.filter((menu) => menu.date === selectedDate),
    [menus, selectedDate],
  );

  const visibleMenus = useMemo(
    () =>
      dateMenus.filter((menu) => {
        if (
          filters.locationId !== "all" &&
          menu.locationId !== filters.locationId
        )
          return false;
        if (
          filters.mealPeriod !== "all" &&
          menu.mealPeriod !== filters.mealPeriod
        )
          return false;
        if (filters.status !== "all" && menu.status !== filters.status)
          return false;
        return true;
      }),
    [dateMenus, filters],
  );

  const active = filtersActive(filters);

  const handleCreate = (input: Parameters<typeof createMenu>[0]) => {
    const menu = createMenu(input);
    setCreateOpen(false);
    navigate(`/menus/${menu.id}/edit`);
  };

  const handleDuplicate = (menu: Menu) => {
    const copy = duplicateMenu(menu.id);
    if (copy) {
      setMessage(
        `Duplicated ${getLocationName(menu.locationId)} ${mealPeriodLabel(
          menu.mealPeriod,
        )} menu for this session.`,
      );
    }
  };

  const handlePublish = (menu: Menu) => {
    const issues = validateMenuForPublish(menu);
    if (issues.length > 0) {
      setMessage(
        `Cannot publish yet — resolve ${issues.length} issue${
          issues.length === 1 ? "" : "s"
        } in the editor first.`,
      );
      return;
    }
    setStatus(menu.id, "published");
    setMessage("Menu published for this session.");
  };

  const handleMarkDraft = (menu: Menu) => {
    setStatus(menu.id, "draft");
    setMessage("Menu moved to draft for this session.");
  };

  const confirmDelete = () => {
    if (pendingDelete) {
      deleteMenu(pendingDelete.id);
      setMessage("Menu deleted for this session.");
      setPendingDelete(null);
    }
  };

  return (
    <div className="p-container-padding space-y-gutter max-w-7xl mx-auto">
      <LiveRegion message={message} />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div>
          <h2 className="font-h2 text-h2">Menus</h2>
          <p className="text-body-sm text-secondary max-w-xl">
            Manage menus by date, dining location, and meal period. All data is
            generic mock data and edits are kept in memory for this session
            only.
          </p>
        </div>
        <Button
          variant="primary"
          icon="add_circle"
          onClick={() => setCreateOpen(true)}
        >
          Create Menu
        </Button>
      </div>

      {/* Date controls */}
      <div className="admin-card p-gutter flex flex-wrap items-center gap-component-gap-md">
        <div className="flex items-center gap-1">
          <Button
            size="sm"
            variant="secondary"
            aria-label="Previous day"
            onClick={() => setSelectedDate(addDaysIso(selectedDate, -1))}
          >
            <Icon name="chevron_left" />
          </Button>
          <Button
            size="sm"
            variant="secondary"
            aria-label="Next day"
            onClick={() => setSelectedDate(addDaysIso(selectedDate, 1))}
          >
            <Icon name="chevron_right" />
          </Button>
        </div>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => setSelectedDate(TODAY_ISO)}
        >
          Today
        </Button>
        <div>
          <label htmlFor="menus-date" className="sr-only">
            Selected date
          </label>
          <input
            id="menus-date"
            type="date"
            className="rounded border border-outline-variant bg-surface-container-lowest px-3 py-1.5 text-body-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
        </div>
        <p className="font-h3 text-h3 ml-auto" aria-live="polite">
          {formatDisplayDate(selectedDate)}
        </p>
      </div>

      <MenuSummaryCards menus={dateMenus} />

      <MenuFilters
        filters={filters}
        onChange={setFilters}
        onClear={() => setFilters(emptyFilters)}
      />

      {/* Menu list / empty states */}
      {dateMenus.length === 0 ? (
        <div className="admin-card p-gutter flex flex-col items-center text-center gap-3 py-12">
          <div className="w-12 h-12 rounded-full bg-primary-fixed text-primary flex items-center justify-center">
            <Icon name="event_busy" />
          </div>
          <h3 className="font-h3 text-h3">No menus for this date</h3>
          <p className="text-body-sm text-secondary max-w-sm">
            There are no menus scheduled for {formatDisplayDate(selectedDate)}.
          </p>
          <Button
            variant="primary"
            icon="add_circle"
            onClick={() => setCreateOpen(true)}
          >
            Create Menu
          </Button>
        </div>
      ) : visibleMenus.length === 0 ? (
        <div className="admin-card p-gutter flex flex-col items-center text-center gap-3 py-12">
          <div className="w-12 h-12 rounded-full bg-primary-fixed text-primary flex items-center justify-center">
            <Icon name="filter_alt" />
          </div>
          <h3 className="font-h3 text-h3">
            No menus match the current filters
          </h3>
          <p className="text-body-sm text-secondary max-w-sm">
            Try adjusting or clearing the filters to see more menus.
          </p>
          {active ? (
            <Button
              variant="secondary"
              icon="filter_alt_off"
              onClick={() => setFilters(emptyFilters)}
            >
              Clear filters
            </Button>
          ) : null}
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-gutter">
          {visibleMenus.map((menu) => (
            <MenuCard
              key={menu.id}
              menu={menu}
              onPreview={(m) => navigate(`/menus/${m.id}/preview`)}
              onEdit={(m) => navigate(`/menus/${m.id}/edit`)}
              onDuplicate={handleDuplicate}
              onMarkDraft={handleMarkDraft}
              onPublish={handlePublish}
              onDelete={(m) => setPendingDelete(m)}
            />
          ))}
        </div>
      )}

      <CreateMenuDialog
        open={createOpen}
        defaultDate={selectedDate}
        onClose={() => setCreateOpen(false)}
        onCreate={handleCreate}
      />

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete menu?"
        message={
          pendingDelete
            ? `This removes the ${getLocationName(
                pendingDelete.locationId,
              )} ${mealPeriodLabel(
                pendingDelete.mealPeriod,
              )} menu for this session. This cannot be undone.`
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
