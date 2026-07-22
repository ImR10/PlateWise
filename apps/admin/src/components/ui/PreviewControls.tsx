import { Button } from "./Button";
import { Icon } from "./Icon";

export type PreviewMode = "desktop" | "mobile";

/** Desktop/Mobile preview device toggle (shared across feature previews). */
export function PreviewDeviceToggle({
  mode,
  onChange,
}: {
  mode: PreviewMode;
  onChange: (mode: PreviewMode) => void;
}) {
  return (
    <div role="group" aria-label="Preview device" className="flex gap-1">
      <Button
        size="sm"
        variant={mode === "desktop" ? "primary" : "secondary"}
        icon="desktop_windows"
        aria-pressed={mode === "desktop"}
        onClick={() => onChange("desktop")}
      >
        Desktop Preview
      </Button>
      <Button
        size="sm"
        variant={mode === "mobile" ? "primary" : "secondary"}
        icon="smartphone"
        aria-pressed={mode === "mobile"}
        onClick={() => onChange("mobile")}
      >
        Mobile Preview
      </Button>
    </div>
  );
}

/** Standard "preview is session-local" notice. */
export function PreviewNotice() {
  return (
    <p
      role="note"
      className="flex items-center gap-2 admin-card p-3 text-body-sm text-secondary"
    >
      <Icon name="info" className="text-[18px] text-primary" />
      Preview only — changes are stored locally for this session.
    </p>
  );
}

/** Returns the frame classes for the student-facing preview container. */
export const previewFrameClass = (mode: PreviewMode): string =>
  mode === "mobile"
    ? "max-w-sm mx-auto border border-outline-variant rounded-xl shadow-sm"
    : "w-full max-w-3xl mx-auto border border-outline-variant rounded-lg";
