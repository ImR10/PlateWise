import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { LocationCard } from "../components/locations/LocationCard";
import {
  LocationFilters,
  emptyLocationFilters,
  locationFiltersActive,
  type LocationFilterState,
} from "../components/locations/LocationFilters";
import { Button } from "../components/ui/Button";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { EmptyState } from "../components/ui/EmptyState";
import { LiveRegion } from "../components/ui/LiveRegion";
import { StatTiles } from "../components/ui/StatTiles";
import type { DiningLocation } from "../data/locationTypes";
import { useDiningLocations } from "../state/DiningLocationsProvider";
import { validateLocationForActivation } from "../state/locationValidation";

export function LocationsPage() {
  const navigate = useNavigate();
  const { locations, duplicate, remove, setStatus } = useDiningLocations();
  const [filters, setFilters] =
    useState<LocationFilterState>(emptyLocationFilters);
  const [pendingDelete, setPendingDelete] = useState<DiningLocation | null>(
    null,
  );
  const [message, setMessage] = useState("");

  const visible = useMemo(() => {
    const term = filters.search.trim().toLowerCase();
    return locations.filter((l) => {
      if (
        l.status === "archived" &&
        !filters.showArchived &&
        filters.status !== "archived"
      )
        return false;
      if (term && !l.name.toLowerCase().includes(term)) return false;
      if (filters.status !== "all" && l.status !== filters.status) return false;
      if (
        filters.mealPeriod !== "all" &&
        !l.mealPeriods.includes(filters.mealPeriod)
      )
        return false;
      return true;
    });
  }, [locations, filters]);

  const tiles = [
    {
      label: "Total Locations",
      value: locations.length,
      accent: "#5b4040",
    },
    {
      label: "Active",
      value: locations.filter((l) => l.status === "active").length,
      accent: "#1e7e34",
    },
    {
      label: "Drafts",
      value: locations.filter((l) => l.status === "draft").length,
      accent: "#94a3b8",
    },
    {
      label: "Archived",
      value: locations.filter((l) => l.status === "archived").length,
      accent: "#dc2626",
    },
  ];

  const handleActivate = (l: DiningLocation) => {
    const issues = validateLocationForActivation(l);
    if (issues.length > 0) {
      setMessage(
        `Cannot activate ${l.name || "location"} — resolve ${
          issues.length
        } issue${issues.length === 1 ? "" : "s"} in the editor first.`,
      );
      return;
    }
    setStatus(l.id, "active");
    setMessage(`${l.name} activated for this session.`);
  };

  const confirmDelete = () => {
    if (pendingDelete) {
      remove(pendingDelete.id);
      setMessage("Dining location deleted for this session.");
      setPendingDelete(null);
    }
  };

  return (
    <div className="p-container-padding space-y-gutter max-w-7xl mx-auto">
      <LiveRegion message={message} />

      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div>
          <h2 className="font-h2 text-h2">Dining Locations</h2>
          <p className="text-body-sm text-secondary max-w-xl">
            Manage dining locations, their service configuration, and operating
            hours. All data is generic mock data kept in memory for this session
            only.
          </p>
        </div>
        <Button
          variant="primary"
          icon="add_circle"
          onClick={() => navigate("/locations/new")}
        >
          Create Dining Location
        </Button>
      </div>

      <StatTiles tiles={tiles} />

      <LocationFilters
        filters={filters}
        onChange={setFilters}
        onClear={() => setFilters(emptyLocationFilters)}
      />

      {locations.length === 0 ? (
        <EmptyState
          icon="location_off"
          title="No dining locations yet"
          message="Create your first dining location to get started."
          action={
            <Button
              variant="primary"
              icon="add_circle"
              onClick={() => navigate("/locations/new")}
            >
              Create Dining Location
            </Button>
          }
        />
      ) : visible.length === 0 ? (
        <EmptyState
          icon="filter_alt"
          title="No dining locations match your filters"
          message="Try adjusting or clearing the filters to see more locations."
          action={
            locationFiltersActive(filters) ? (
              <Button
                variant="secondary"
                icon="filter_alt_off"
                onClick={() => setFilters(emptyLocationFilters)}
              >
                Clear filters
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-gutter">
          {visible.map((location) => (
            <LocationCard
              key={location.id}
              location={location}
              onEdit={(l) => navigate(`/locations/${l.id}/edit`)}
              onPreview={(l) => navigate(`/locations/${l.id}/preview`)}
              onDuplicate={(l) => {
                duplicate(l.id);
                setMessage(`Duplicated ${l.name} for this session.`);
              }}
              onActivate={handleActivate}
              onMoveDraft={(l) => {
                setStatus(l.id, "draft");
                setMessage(`${l.name} moved to draft for this session.`);
              }}
              onArchive={(l) => {
                setStatus(l.id, "archived");
                setMessage(`${l.name} archived for this session.`);
              }}
              onRestore={(l) => {
                setStatus(l.id, "draft");
                setMessage(`${l.name} restored to draft for this session.`);
              }}
              onDelete={(l) => setPendingDelete(l)}
            />
          ))}
        </div>
      )}

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete dining location?"
        message={
          pendingDelete
            ? `This permanently removes ${
                pendingDelete.name || "this location"
              } for this session. This cannot be undone.`
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
