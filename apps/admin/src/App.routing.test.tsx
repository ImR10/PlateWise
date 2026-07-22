import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";
import { renderWithRouter } from "./test/renderWithRouter";

describe("Routing", () => {
  it("redirects '/' to the dashboard", () => {
    renderWithRouter(<App />, { route: "/" });

    expect(
      screen.getByRole("heading", { name: "Are today's menus ready?" }),
    ).toBeInTheDocument();
  });

  it("renders the dashboard at '/dashboard'", () => {
    renderWithRouter(<App />, { route: "/dashboard" });

    expect(
      screen.getByRole("heading", { name: "Are today's menus ready?" }),
    ).toBeInTheDocument();
  });

  it.each([
    ["/menus", "Menus"],
    ["/locations", "Dining Locations"],
    ["/foods", "Food Catalog"],
    ["/activity", "Activity"],
    ["/settings", "Settings"],
  ])("renders an intentional placeholder for %s", (route, title) => {
    renderWithRouter(<App />, { route });

    // The page body heading (h2) — distinct from the top-bar h1 of the same name.
    expect(
      screen.getByRole("heading", { name: title, level: 2 }),
    ).toBeInTheDocument();
    expect(screen.getByText("Not yet implemented")).toBeInTheDocument();
  });

  it("renders a not-found placeholder for unknown routes", () => {
    renderWithRouter(<App />, { route: "/nope" });

    expect(
      screen.getByRole("heading", { name: "Page Not Found" }),
    ).toBeInTheDocument();
  });
});
