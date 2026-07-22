import { Icon } from "../components/ui/Icon";

interface PlaceholderPageProps {
  title: string;
  description: string;
  icon: string;
}

/**
 * Intentional placeholder for routes that are not part of this milestone.
 * Communicates clearly that the feature is not yet implemented rather than
 * presenting a fake interface.
 */
export function PlaceholderPage({
  title,
  description,
  icon,
}: PlaceholderPageProps) {
  return (
    <div className="p-container-padding max-w-7xl mx-auto">
      <div className="admin-card p-gutter flex flex-col items-center justify-center text-center gap-3 py-16">
        <div className="w-12 h-12 rounded-full bg-primary-fixed text-primary flex items-center justify-center">
          <Icon name={icon} />
        </div>
        <h2 className="font-h2 text-h2">{title}</h2>
        <p className="text-body-md text-secondary max-w-md">{description}</p>
        <span className="status-pill badge-neutral">Not yet implemented</span>
      </div>
    </div>
  );
}
