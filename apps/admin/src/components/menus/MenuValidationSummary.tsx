import type { MenuValidationIssue } from "../../data/menuTypes";
import { Icon } from "../ui/Icon";

/**
 * Error summary shown when a publish attempt fails validation. Rendered as an
 * alert so assistive tech announces it, and each issue names the affected area.
 */
export function MenuValidationSummary({
  issues,
}: {
  issues: MenuValidationIssue[];
}) {
  if (issues.length === 0) return null;

  return (
    <div
      role="alert"
      className="admin-card p-gutter border-l-4 border-error bg-error-container/40"
    >
      <p className="flex items-center gap-2 font-h3 text-h3 text-on-error-container">
        <Icon name="error" className="text-error" />
        Resolve {issues.length} issue{issues.length === 1 ? "" : "s"} before
        publishing
      </p>
      <ul className="list-disc pl-8 mt-2 space-y-1 text-body-md">
        {issues.map((issue) => (
          <li key={issue.id}>{issue.message}</li>
        ))}
      </ul>
    </div>
  );
}
