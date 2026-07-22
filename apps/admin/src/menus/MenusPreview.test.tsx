import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import App from "../App";
import { renderWithRouter } from "../test/renderWithRouter";

describe("Menu preview", () => {
  it("hides internal notes and internal title", () => {
    renderWithRouter(<App />, { route: "/menus/menu-a-breakfast/preview" });
    expect(screen.queryByText(/Internal setup note/)).not.toBeInTheDocument();
    expect(screen.queryByText("Morning service")).not.toBeInTheDocument();
  });

  it("renders stations and items", () => {
    renderWithRouter(<App />, { route: "/menus/menu-a-breakfast/preview" });
    expect(screen.getByText("Station A")).toBeInTheDocument();
    expect(screen.getByText("Station B")).toBeInTheDocument();
    expect(screen.getByText("Menu Item 01")).toBeInTheDocument();
  });

  it("toggles between desktop and mobile preview", async () => {
    const user = userEvent.setup();
    renderWithRouter(<App />, { route: "/menus/menu-a-breakfast/preview" });

    const desktop = screen.getByRole("button", { name: "Desktop Preview" });
    const mobile = screen.getByRole("button", { name: "Mobile Preview" });
    expect(desktop).toHaveAttribute("aria-pressed", "true");
    expect(mobile).toHaveAttribute("aria-pressed", "false");

    await user.click(mobile);

    expect(
      screen.getByRole("button", { name: "Mobile Preview" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(
      screen.getByRole("button", { name: "Desktop Preview" }),
    ).toHaveAttribute("aria-pressed", "false");
  });

  it("toggles visibility of unavailable items", async () => {
    const user = userEvent.setup();
    renderWithRouter(<App />, { route: "/menus/menu-a-lunch/preview" });

    // Menu Item 05 is unavailable and hidden by default.
    expect(screen.queryByText("Menu Item 05")).not.toBeInTheDocument();

    await user.click(screen.getByLabelText("Show unavailable items"));

    expect(screen.getByText("Menu Item 05")).toBeInTheDocument();
  });
});
