import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "../App";
import { renderWithRouter } from "../test/renderWithRouter";

describe("Menus routing", () => {
  it("renders the menus overview at /menus", () => {
    renderWithRouter(<App />, { route: "/menus" });
    expect(
      screen.getByText(/Manage menus by date, dining location/),
    ).toBeInTheDocument();
  });

  it("renders the editor for a valid menu id", () => {
    renderWithRouter(<App />, { route: "/menus/menu-a-breakfast/edit" });
    expect(
      screen.getByRole("heading", { name: "Menu details" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Back to menus/ }),
    ).toBeInTheDocument();
  });

  it("renders the preview for a valid menu id", () => {
    renderWithRouter(<App />, { route: "/menus/menu-a-breakfast/preview" });
    expect(
      screen.getByText(/Preview only — changes are stored locally/),
    ).toBeInTheDocument();
    // "Sample University" appears in the sidebar and the preview header.
    expect(screen.getAllByText("Sample University").length).toBeGreaterThan(0);
  });

  it("shows a not-found state for an invalid menu id in the editor", () => {
    renderWithRouter(<App />, { route: "/menus/does-not-exist/edit" });
    expect(
      screen.getByRole("heading", { name: "Menu not found" }),
    ).toBeInTheDocument();
  });

  it("shows a not-found state for an invalid menu id in the preview", () => {
    renderWithRouter(<App />, { route: "/menus/does-not-exist/preview" });
    expect(
      screen.getByRole("heading", { name: "Menu not found" }),
    ).toBeInTheDocument();
  });
});
