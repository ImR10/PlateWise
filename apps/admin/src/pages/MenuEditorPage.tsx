import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { FoodCatalogDialog } from "../components/menus/FoodCatalogDialog";
import { MenuEditorHeader } from "../components/menus/MenuEditorHeader";
import { MenuNotFound } from "../components/menus/MenuNotFound";
import { MenuStationSection } from "../components/menus/MenuStationSection";
import { MenuValidationSummary } from "../components/menus/MenuValidationSummary";
import { Button } from "../components/ui/Button";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { LiveRegion } from "../components/ui/LiveRegion";
import { diningLocations } from "../data/locations";
import {
  MEAL_PERIODS,
  type MealPeriod,
  type MenuStation,
  type MenuValidationIssue,
} from "../data/menuTypes";
import { useMenus } from "../state/MenusProvider";
import { validateMenuForPublish } from "../state/menuValidation";

const fieldClass =
  "w-full rounded border border-outline-variant bg-surface-container-lowest px-3 py-2 text-body-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary";
const labelClass = "block text-label-md text-secondary uppercase mb-1";

export function MenuEditorPage() {
  const { menuId } = useParams();
  const navigate = useNavigate();
  const menus = useMenus();
  const menu = menuId ? menus.getMenu(menuId) : undefined;

  const [dirty, setDirty] = useState(false);
  const [issues, setIssues] = useState<MenuValidationIssue[]>([]);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [foodDialog, setFoodDialog] = useState<{
    open: boolean;
    stationId: string;
  }>({ open: false, stationId: "" });
  const [pendingStation, setPendingStation] = useState<MenuStation | null>(
    null,
  );
  const [leaveOpen, setLeaveOpen] = useState(false);
  const [message, setMessage] = useState("");

  if (!menu) return <MenuNotFound />;

  // Wrap any edit so it flags unsaved changes and clears stale validation.
  const edit = (fn: () => void) => {
    fn();
    setDirty(true);
    setIssues([]);
  };

  const toggleCollapsed = (stationId: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(stationId)) next.delete(stationId);
      else next.add(stationId);
      return next;
    });
  };

  const stationOptions = menu.stations.map((s) => ({ id: s.id, name: s.name }));

  const goBack = () => {
    if (dirty) setLeaveOpen(true);
    else navigate("/menus");
  };

  const saveDraft = () => {
    menus.setStatus(menu.id, "draft");
    setDirty(false);
    setIssues([]);
    setMessage("Draft updated for this session.");
  };

  const publish = () => {
    const found = validateMenuForPublish(menu);
    if (found.length > 0) {
      setIssues(found);
      setMessage(
        `Cannot publish — resolve ${found.length} issue${
          found.length === 1 ? "" : "s"
        } below.`,
      );
      return;
    }
    menus.setStatus(menu.id, "published");
    setDirty(false);
    setIssues([]);
    setMessage("Menu published for this session.");
  };

  return (
    <div className="p-container-padding space-y-gutter max-w-7xl mx-auto">
      <LiveRegion message={message} />

      <MenuEditorHeader
        menu={menu}
        dirty={dirty}
        onBack={goBack}
        onPreview={() => navigate(`/menus/${menu.id}/preview`)}
        onSaveDraft={saveDraft}
        onPublish={publish}
      />

      <MenuValidationSummary issues={issues} />

      {/* Editable metadata */}
      <section className="admin-card p-gutter" aria-labelledby="meta-heading">
        <h3 id="meta-heading" className="font-h3 text-h3 mb-4">
          Menu details
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-component-gap-md">
          <div>
            <label htmlFor="meta-location" className={labelClass}>
              Dining location
            </label>
            <select
              id="meta-location"
              className={fieldClass}
              value={menu.locationId}
              onChange={(e) =>
                edit(() =>
                  menus.updateMeta(menu.id, { locationId: e.target.value }),
                )
              }
            >
              <option value="">Select a location</option>
              {diningLocations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="meta-date" className={labelClass}>
              Date
            </label>
            <input
              id="meta-date"
              type="date"
              className={fieldClass}
              value={menu.date}
              onChange={(e) =>
                edit(() => menus.updateMeta(menu.id, { date: e.target.value }))
              }
            />
          </div>
          <div>
            <label htmlFor="meta-meal" className={labelClass}>
              Meal period
            </label>
            <select
              id="meta-meal"
              className={fieldClass}
              value={menu.mealPeriod}
              onChange={(e) =>
                edit(() =>
                  menus.updateMeta(menu.id, {
                    mealPeriod: e.target.value as MealPeriod,
                  }),
                )
              }
            >
              {MEAL_PERIODS.map((meal) => (
                <option key={meal.value} value={meal.value}>
                  {meal.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="meta-title" className={labelClass}>
              Internal menu title
            </label>
            <input
              id="meta-title"
              type="text"
              className={fieldClass}
              value={menu.title}
              onChange={(e) =>
                edit(() => menus.updateMeta(menu.id, { title: e.target.value }))
              }
            />
          </div>
          <div className="md:col-span-2">
            <label htmlFor="meta-notes" className={labelClass}>
              Internal notes (not student-facing)
            </label>
            <textarea
              id="meta-notes"
              rows={2}
              className={fieldClass}
              value={menu.internalNotes ?? ""}
              placeholder="Only visible to staff — never shown to students."
              onChange={(e) =>
                edit(() =>
                  menus.updateMeta(menu.id, { internalNotes: e.target.value }),
                )
              }
            />
          </div>
        </div>
      </section>

      {/* Stations */}
      <div className="flex items-center justify-between">
        <h3 className="font-h3 text-h3">Stations</h3>
        <Button
          variant="secondary"
          icon="add"
          onClick={() => edit(() => menus.addStation(menu.id))}
        >
          Add Station
        </Button>
      </div>

      {menu.stations.length === 0 ? (
        <div className="admin-card p-gutter text-center text-body-sm text-secondary py-8">
          No stations yet. Add a station to start building this menu.
        </div>
      ) : (
        <div className="space-y-gutter">
          {menu.stations.map((station, index) => (
            <MenuStationSection
              key={station.id}
              station={station}
              index={index}
              count={menu.stations.length}
              stations={stationOptions}
              collapsed={collapsed.has(station.id)}
              onToggleCollapse={() => toggleCollapsed(station.id)}
              onRename={(name) =>
                edit(() => menus.renameStation(menu.id, station.id, name))
              }
              onDelete={() => setPendingStation(station)}
              onMoveUp={() =>
                edit(() => menus.moveStation(menu.id, station.id, -1))
              }
              onMoveDown={() =>
                edit(() => menus.moveStation(menu.id, station.id, 1))
              }
              onAddItem={() =>
                setFoodDialog({ open: true, stationId: station.id })
              }
              onUpdateItem={(itemId, patch) =>
                edit(() => menus.updateItem(menu.id, station.id, itemId, patch))
              }
              onSetItemAvailability={(itemId, availability) =>
                edit(() =>
                  menus.setItemAvailability(
                    menu.id,
                    station.id,
                    itemId,
                    availability,
                  ),
                )
              }
              onMoveItem={(itemId, direction) =>
                edit(() =>
                  menus.moveItem(menu.id, station.id, itemId, direction),
                )
              }
              onMoveItemToStation={(itemId, toStationId) =>
                edit(() =>
                  menus.moveItemToStation(
                    menu.id,
                    station.id,
                    itemId,
                    toStationId,
                  ),
                )
              }
              onRemoveItem={(itemId) =>
                edit(() => menus.removeItem(menu.id, station.id, itemId))
              }
            />
          ))}
        </div>
      )}

      <FoodCatalogDialog
        open={foodDialog.open}
        stations={stationOptions}
        defaultStationId={foodDialog.stationId}
        onClose={() => setFoodDialog({ open: false, stationId: "" })}
        onAdd={(stationId, items) => {
          edit(() => menus.addItems(menu.id, stationId, items));
          setFoodDialog({ open: false, stationId: "" });
          setMessage(
            `${items.length} item${
              items.length === 1 ? "" : "s"
            } added for this session.`,
          );
        }}
      />

      <ConfirmDialog
        open={pendingStation !== null}
        title="Delete station?"
        message={
          pendingStation
            ? `This removes "${
                pendingStation.name || "this station"
              }" and its items for this session.`
            : ""
        }
        confirmLabel="Delete"
        destructive
        onConfirm={() => {
          if (pendingStation) {
            edit(() => menus.deleteStation(menu.id, pendingStation.id));
            setPendingStation(null);
          }
        }}
        onCancel={() => setPendingStation(null)}
      />

      <ConfirmDialog
        open={leaveOpen}
        title="Discard unsaved changes?"
        message="You have unsaved changes for this session. Leaving will keep them in memory but you'll return to the menus list."
        confirmLabel="Leave"
        cancelLabel="Stay"
        onConfirm={() => {
          setLeaveOpen(false);
          navigate("/menus");
        }}
        onCancel={() => setLeaveOpen(false)}
      />
    </div>
  );
}
