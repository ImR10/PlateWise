import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { navItems } from "../../data/dashboard";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

/**
 * Application shell: fixed sidebar + sticky top bar + routed content.
 * Manages the responsive off-canvas drawer state for narrow viewports.
 */
export function AdminLayout() {
  const location = useLocation();
  const [isSidebarOpen, setSidebarOpen] = useState(false);

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  // Allow Escape to dismiss the open drawer.
  useEffect(() => {
    if (!isSidebarOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSidebarOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isSidebarOpen]);

  // Match the current path to a nav item, including nested routes such as
  // /menus/:id/edit. Prefer the longest matching base path.
  const activeNav = [...navItems]
    .filter(
      (item) =>
        location.pathname === item.path ||
        location.pathname.startsWith(`${item.path}/`),
    )
    .sort((a, b) => b.path.length - a.path.length)[0];
  const pageTitle = activeNav?.label ?? "Dashboard";

  return (
    <div className="min-h-screen">
      <Sidebar isOpen={isSidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Backdrop for the mobile drawer */}
      {isSidebarOpen ? (
        <button
          type="button"
          aria-label="Close navigation menu"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
        />
      ) : null}

      <div className="lg:ml-sidebar-width min-h-screen flex flex-col">
        <TopBar
          title={pageTitle}
          isSidebarOpen={isSidebarOpen}
          onMenuClick={() => setSidebarOpen(true)}
        />
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
