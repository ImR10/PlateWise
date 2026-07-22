import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { LocationForm } from "../components/locations/LocationForm";
import { Button } from "../components/ui/Button";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { EmptyState } from "../components/ui/EmptyState";
import { Icon } from "../components/ui/Icon";
import { LiveRegion } from "../components/ui/LiveRegion";
import { StatusBadge } from "../components/ui/StatusBadge";
import { ValidationSummary } from "../components/ui/ValidationSummary";
import {
  locationStatusLabel,
  locationStatusTone,
  type DiningLocation,
  type LocationStation,
} from "../data/locationTypes";
import { buildLocation } from "../state/locationOps";
import { useDiningLocations } from "../state/DiningLocationsProvider";
import {
  validateLocationForActivation,
  type ValidationIssue,
} from "../state/locationValidation";

export function LocationFormPage() {
  const { locationId } = useParams();
  const navigate = useNavigate();
  const store = useDiningLocations();
  const isCreate = !locationId;

  const [draft, setDraft] = useState<DiningLocation>(() => buildLocation());
  const [dirty, setDirty] = useState(false);
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [pendingStation, setPendingStation] = useState<LocationStation | null>(
    null,
  );
  const [leaveOpen, setLeaveOpen] = useState(false);
  const [message, setMessage] = useState("");

  const existing = locationId ? store.getLocation(locationId) : undefined;

  if (!isCreate && !existing) {
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

  const location = isCreate ? draft : (existing as DiningLocation);

  const update = (fn: (l: DiningLocation) => DiningLocation) => {
    if (isCreate) setDraft((d) => fn(d));
    else store.updateWith(location.id, fn);
    setDirty(true);
    setIssues([]);
  };

  const commitCreate = (status: DiningLocation["status"]) => {
    store.create({
      ...draft,
      status,
      updatedAt: "Just now",
      updatedBy: "John Doe",
    });
    navigate("/locations");
  };

  const saveDraft = () => {
    if (isCreate) {
      commitCreate("draft");
      return;
    }
    store.setStatus(location.id, "draft");
    setDirty(false);
    setIssues([]);
    setMessage("Draft updated for this session.");
  };

  const activate = () => {
    const found = validateLocationForActivation(location);
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
    store.setStatus(location.id, "active");
    setDirty(false);
    setIssues([]);
    setMessage("Dining location activated for this session.");
  };

  const goBack = () => {
    if (dirty) setLeaveOpen(true);
    else navigate("/locations");
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
          Back to dining locations
        </button>

        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="font-h2 text-h2">
              {isCreate
                ? "New dining location"
                : location.name.trim() || "Untitled location"}
            </h2>
            <StatusBadge tone={locationStatusTone[location.status]}>
              {locationStatusLabel(location.status)}
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
                onClick={() => navigate(`/locations/${location.id}/preview`)}
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

      <LocationForm
        location={location}
        update={update}
        onRemoveStation={(station) => setPendingStation(station)}
      />

      <ConfirmDialog
        open={pendingStation !== null}
        title="Remove station?"
        message={
          pendingStation
            ? `This removes "${
                pendingStation.name || "this station"
              }" from the location for this session.`
            : ""
        }
        confirmLabel="Remove"
        destructive
        onConfirm={() => {
          if (pendingStation) {
            update((l) => ({
              ...l,
              stations: l.stations.filter((s) => s.id !== pendingStation.id),
            }));
            setPendingStation(null);
          }
        }}
        onCancel={() => setPendingStation(null)}
      />

      <ConfirmDialog
        open={leaveOpen}
        title="Discard unsaved changes?"
        message="You have unsaved changes for this session. Leaving will return you to the dining locations list."
        confirmLabel="Leave"
        cancelLabel="Stay"
        onConfirm={() => {
          setLeaveOpen(false);
          navigate("/locations");
        }}
        onCancel={() => setLeaveOpen(false)}
      />
    </div>
  );
}
