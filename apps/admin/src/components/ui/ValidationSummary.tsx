import type { ValidationIssue } from "../../state/locationValidation";
import { Icon } from "./Icon";

/**
 * Accessible error summary shown when an activate/publish attempt fails
 * validation. Rendered as an alert so assistive tech announces it.
 */
export function ValidationSummary({
  issues,
  heading = "Resolve these issues before continuing",
}: {
  issues: ValidationIssue[];
  heading?: string;
}) {
  if (issues.length === 0) return null;

  return (
    <div
      role="alert"
      className="admin-card p-gutter border-l-4 border-error bg-error-container/40"
    >
      <p className="flex items-center gap-2 font-h3 text-h3 text-on-error-container">
        <Icon name="error" className="text-error" />
        {heading}
      </p>
      <ul className="list-disc pl-8 mt-2 space-y-1 text-body-md">
        {issues.map((issue) => (
          <li key={issue.id}>{issue.message}</li>
        ))}
      </ul>
    </div>
  );
}
