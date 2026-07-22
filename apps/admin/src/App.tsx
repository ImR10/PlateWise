import { Navigate, Route, Routes } from "react-router-dom";

import { AdminLayout } from "./components/layout/AdminLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AdminLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route
          path="/menus"
          element={
            <PlaceholderPage
              title="Menus"
              icon="restaurant_menu"
              description="Build, schedule, and publish dining-hall menus. This workspace arrives in a later milestone."
            />
          }
        />
        <Route
          path="/locations"
          element={
            <PlaceholderPage
              title="Dining Locations"
              icon="location_on"
              description="Manage University of Georgia dining locations and their menu readiness. Coming in a later milestone."
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
