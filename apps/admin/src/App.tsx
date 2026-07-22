import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { AdminLayout } from "./components/layout/AdminLayout";
import { AnalysisPage } from "./pages/AnalysisPage";
import { DashboardPage } from "./pages/DashboardPage";
import { FoodFormPage } from "./pages/FoodFormPage";
import { FoodPreviewPage } from "./pages/FoodPreviewPage";
import { FoodsPage } from "./pages/FoodsPage";
import { LocationFormPage } from "./pages/LocationFormPage";
import { LocationPreviewPage } from "./pages/LocationPreviewPage";
import { LocationsPage } from "./pages/LocationsPage";
import { MenuEditorPage } from "./pages/MenuEditorPage";
import { MenuPreviewPage } from "./pages/MenuPreviewPage";
import { MenusPage } from "./pages/MenusPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { DiningLocationsProvider } from "./state/DiningLocationsProvider";
import { FoodCatalogProvider } from "./state/FoodCatalogProvider";
import { MenusProvider } from "./state/MenusProvider";

export default function App() {
  return (
    // Dining locations and food catalog are shared, in-memory managed records
    // that the Menus feature also consumes. Providing them at the top keeps a
    // single source of truth across all three features for the session.
    <DiningLocationsProvider>
      <FoodCatalogProvider>
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
              <Route
                path="/menus/:menuId/preview"
                element={<MenuPreviewPage />}
              />
            </Route>

            {/* Dining Locations feature */}
            <Route path="/locations" element={<LocationsPage />} />
            <Route path="/locations/new" element={<LocationFormPage />} />
            <Route
              path="/locations/:locationId/edit"
              element={<LocationFormPage />}
            />
            <Route
              path="/locations/:locationId/preview"
              element={<LocationPreviewPage />}
            />

            {/* Food Catalog feature */}
            <Route path="/foods" element={<FoodsPage />} />
            <Route path="/foods/new" element={<FoodFormPage />} />
            <Route path="/foods/:foodId/edit" element={<FoodFormPage />} />
            <Route
              path="/foods/:foodId/preview"
              element={<FoodPreviewPage />}
            />

            {/* Analysis feature */}
            <Route path="/analysis" element={<AnalysisPage />} />

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
      </FoodCatalogProvider>
    </DiningLocationsProvider>
  );
}
