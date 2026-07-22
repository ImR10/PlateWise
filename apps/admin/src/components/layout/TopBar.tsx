import { currentDate, institution } from "../../data/dashboard";
import { Icon } from "../ui/Icon";

interface TopBarProps {
  title: string;
  isSidebarOpen: boolean;
  onMenuClick: () => void;
}

const iconButton =
  "text-secondary hover:text-primary transition-colors motion-reduce:transition-none rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2";

/** Sticky top application bar with page title, date, and utility controls. */
export function TopBar({ title, isSidebarOpen, onMenuClick }: TopBarProps) {
  return (
    <header className="flex justify-between items-center h-14 px-gutter border-b border-outline-variant sticky top-0 bg-surface-bright z-40">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Open navigation menu"
          aria-controls="primary-sidebar"
          aria-expanded={isSidebarOpen}
          className={`lg:hidden ${iconButton}`}
        >
          <Icon name="menu" />
        </button>
        <h1 className="font-h1 text-h1 text-on-surface">{title}</h1>
      </div>
      <div className="flex items-center gap-6">
        <span className="font-label-md text-label-md text-secondary hidden sm:inline">
          {currentDate}
        </span>
        <div className="flex items-center gap-4">
          <button
            type="button"
            aria-label="Notifications"
            className={iconButton}
          >
            <Icon name="notifications" />
          </button>
          <button type="button" aria-label="Help" className={iconButton}>
            <Icon name="help_outline" />
          </button>
          <div
            className="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center text-white font-bold text-xs"
            title={institution.name}
            aria-label={institution.name}
            role="img"
          >
            {institution.shortCode}
          </div>
        </div>
      </div>
    </header>
  );
}
