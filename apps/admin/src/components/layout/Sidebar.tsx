import { NavLink } from "react-router-dom";

import { institution, navItems, staffProfile } from "../../data/dashboard";
import { Icon } from "../ui/Icon";

interface SidebarProps {
  /** Whether the off-canvas drawer is open (mobile/tablet only). */
  isOpen: boolean;
  onClose: () => void;
}

const linkBase =
  "flex items-center gap-3 px-3 py-2 rounded transition-colors duration-200 motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2";

/**
 * Primary navigation rail. Fixed on large screens; on smaller widths it
 * becomes an off-canvas drawer driven by `isOpen` and closed via `onClose`.
 */
export function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <aside
      id="primary-sidebar"
      aria-label="Primary"
      className={[
        "w-sidebar-width h-screen fixed left-0 top-0 z-50 flex flex-col py-gutter px-component-gap-md",
        "bg-surface border-r border-outline-variant",
        "transition-transform duration-200 motion-reduce:transition-none lg:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full",
      ].join(" ")}
    >
      <div className="mb-8 px-2 flex items-start justify-between">
        <div>
          <h2 className="font-h2 text-h2 text-primary">PlateWise Admin</h2>
          <p className="text-body-sm text-secondary">{institution.name}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close navigation menu"
          className="lg:hidden text-secondary hover:text-primary rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <Icon name="close" />
        </button>
      </div>

      <nav aria-label="Primary navigation" className="flex-1 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={onClose}
            className={({ isActive }) =>
              [
                linkBase,
                isActive
                  ? "text-primary bg-primary-fixed font-bold"
                  : "text-secondary hover:text-on-surface hover:bg-surface-container-high",
              ].join(" ")
            }
          >
            <Icon name={item.icon} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto pt-6 border-t border-outline-variant">
        <div className="flex items-center gap-3 px-3 py-2">
          <div
            className="w-8 h-8 rounded-full bg-surface-container-high flex items-center justify-center font-bold text-[11px] shrink-0"
            aria-hidden="true"
          >
            {staffProfile.initials}
          </div>
          <div className="min-w-0">
            <p className="font-body-sm font-bold text-on-surface truncate">
              {staffProfile.name}
            </p>
            <p className="text-[11px] text-secondary truncate">
              {staffProfile.role}
            </p>
          </div>
        </div>
        <a
          href="#sign-out"
          className={`${linkBase} text-secondary hover:text-on-surface`}
        >
          <Icon name="logout" />
          <span>Sign Out</span>
        </a>
      </div>
    </aside>
  );
}
