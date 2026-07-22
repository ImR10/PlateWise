import { Link } from "react-router-dom";

import { Icon } from "../ui/Icon";

/** Not-found state shown inside the admin layout for invalid menu IDs. */
export function MenuNotFound() {
  return (
    <div className="p-container-padding max-w-7xl mx-auto">
      <div className="admin-card p-gutter flex flex-col items-center text-center gap-3 py-16">
        <div className="w-12 h-12 rounded-full bg-primary-fixed text-primary flex items-center justify-center">
          <Icon name="error" />
        </div>
        <h2 className="font-h2 text-h2">Menu not found</h2>
        <p className="text-body-md text-secondary max-w-md">
          We couldn&apos;t find a menu with that ID. It may have been deleted
          this session, or the link is invalid.
        </p>
        <Link
          to="/menus"
          className="inline-flex items-center gap-1 text-primary font-bold rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <Icon name="arrow_back" className="text-[18px]" />
          Back to menus
        </Link>
      </div>
    </div>
  );
}
