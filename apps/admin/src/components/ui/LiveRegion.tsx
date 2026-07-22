/**
 * Visually hidden polite live region for announcing transient status feedback
 * (e.g. "Menu published for this session.") to assistive technology.
 */
export function LiveRegion({ message }: { message: string }) {
  return (
    <div aria-live="polite" role="status" className="sr-only">
      {message}
    </div>
  );
}
