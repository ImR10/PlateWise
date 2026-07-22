import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { LocationPreview } from "../components/locations/LocationPreview";
import { EmptyState } from "../components/ui/EmptyState";
import { Icon } from "../components/ui/Icon";
import {
  PreviewDeviceToggle,
  PreviewNotice,
  type PreviewMode,
} from "../components/ui/PreviewControls";
import { StatusBadge } from "../components/ui/StatusBadge";
import { locationStatusLabel, locationStatusTone } from "../data/locationTypes";
import { useDiningLocations } from "../state/DiningLocationsProvider";

export function LocationPreviewPage() {
  const { locationId } = useParams();
  const navigate = useNavigate();
  const { getLocation } = useDiningLocations();
  const location = locationId ? getLocation(locationId) : undefined;
  const [mode, setMode] = useState<PreviewMode>("desktop");

  if (!location) {
    return (
      <div className="p-container-padding max-w-7xl mx-auto">
        <EmptyState
          icon="error"
          title="Dining location not found"
          message="We couldn't find a dining location with that ID. It may have been deleted this session, or the link is invalid."
          action={
            <Link
              to="/locations"
              className="inline-flex items-center gap-1 text-primary font-bold rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              <Icon name="arrow_back" className="text-[18px]" />
              Back to dining locations
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
          onClick={() => navigate(`/locations/${location.id}/edit`)}
          className="inline-flex items-center gap-1 text-primary font-bold text-body-sm rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <Icon name="arrow_back" className="text-[18px]" />
          Back to editor
        </button>
        <button
          type="button"
          onClick={() => navigate("/locations")}
          className="inline-flex items-center gap-1 text-secondary font-bold text-body-sm rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <Icon name="list" className="text-[18px]" />
          Back to dining locations
        </button>
      </div>

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="font-h2 text-h2">
            {location.name.trim() || "Untitled location"}
          </h2>
          <StatusBadge tone={locationStatusTone[location.status]}>
            {locationStatusLabel(location.status)}
          </StatusBadge>
        </div>
        <PreviewDeviceToggle mode={mode} onChange={setMode} />
      </div>

      <PreviewNotice />

      <LocationPreview location={location} mode={mode} />
    </div>
  );
}
