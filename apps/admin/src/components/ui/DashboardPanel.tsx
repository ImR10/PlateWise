import type { ReactNode } from "react";

interface DashboardPanelProps {
  /** Optional panel heading. Omit to supply a fully custom header via children. */
  title?: string;
  /** Heading level for the title (defaults to h3). */
  titleLevel?: "h2" | "h3";
  /** Element rendered on the trailing edge of the header row. */
  headerAccessory?: ReactNode;
  /**
   * When true the title row sits in its own bordered header band and the
   * children render flush beneath it (used by the "Needs Attention" panel).
   * Otherwise the title and children share a single padded body.
   */
  headerBordered?: boolean;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
}

/** Reusable white card container matching the approved dashboard panels. */
export function DashboardPanel({
  title,
  titleLevel = "h3",
  headerAccessory,
  headerBordered = false,
  className,
  bodyClassName,
  children,
}: DashboardPanelProps) {
  const Heading = titleLevel;
  const headingClass =
    titleLevel === "h2" ? "font-h2 text-h2" : "font-h3 text-h3";

  if (headerBordered) {
    return (
      <section
        className={`admin-card flex flex-col${className ? ` ${className}` : ""}`}
      >
        <div className="p-gutter border-b border-outline-variant flex justify-between items-center gap-3">
          {title ? <Heading className={headingClass}>{title}</Heading> : null}
          {headerAccessory}
        </div>
        <div className={bodyClassName}>{children}</div>
      </section>
    );
  }

  return (
    <section
      className={`admin-card p-gutter${className ? ` ${className}` : ""}`}
    >
      {title || headerAccessory ? (
        <div className="flex justify-between items-center gap-3 mb-4">
          {title ? <Heading className={headingClass}>{title}</Heading> : null}
          {headerAccessory}
        </div>
      ) : null}
      <div className={bodyClassName}>{children}</div>
    </section>
  );
}
