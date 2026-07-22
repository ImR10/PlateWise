import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { AdminLayout } from "./components/layout/AdminLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { MenuEditorPage } from "./pages/MenuEditorPage";
import { MenuPreviewPage } from "./pages/MenuPreviewPage";
import { MenusPage } from "./pages/MenusPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { MenusProvider } from "./state/MenusProvider";

export default function App() {
  return (
    <Routes>
      <Route element={<AdminLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        {/* Menus feature — shares an in-memory provider across its routes. */}
        <Route
          element={
            <MenusProvider>
              <Outlet />
            </MenusProvider>
          }
        >
          <Route path="/menus" element={<MenusPage />} />
          <Route path="/menus/:menuId/edit" element={<MenuEditorPage />} />
          <Route path="/menus/:menuId/preview" element={<MenuPreviewPage />} />
        </Route>
        <Route
          path="/locations"
          element={
            <PlaceholderPage
              title="Dining Locations"
              icon="location_on"
              description="Manage Sample University dining locations and their menu readiness. Coming in a later milestone."
            />
          }
        />
        <Route
          path="/foods"
          element={
            <PlaceholderPage
              title="Food Catalog"
              icon="inventory_2"
              description="Maintain the shared catalog of foods, allergens, and nutrition. Coming in a later milestone."
            />
          }
        />
        <Route
          path="/activity"
          element={
            <PlaceholderPage
              title="Activity"
              icon="history"
              description="Review the full history of staff and system actions. Coming in a later milestone."
            />
          }
        />
        <Route
          path="/settings"
          element={
            <PlaceholderPage
              title="Settings"
              icon="settings"
              description="Configure dining program preferences and staff access. Coming in a later milestone."
            />
          }
        />
        <Route
          path="*"
          element={
            <PlaceholderPage
              title="Page Not Found"
              icon="error"
              description="We couldn't find that page. Use the navigation to return to the dashboard."
            />
          }
        />
      </Route>
    </Routes>
  );
}
