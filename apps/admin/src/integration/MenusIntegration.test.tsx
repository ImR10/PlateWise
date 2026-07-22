import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import App from "../App";
import { renderWithRouter } from "../test/renderWithRouter";

describe("Menus integration with managed records", () => {
  it("excludes archived food items from the menu catalog picker but keeps active ones", async () => {
    const user = userEvent.setup();
    // menu-a-breakfast has stations to add items to.
    renderWithRouter(<App />, { route: "/menus/menu-a-breakfast/edit" });

    await user.click(
      screen.getAllByRole("button", { name: "Add Food Item" })[0],
    );
    const dialog = screen.getByRole("dialog");

    // Active catalog item is offered.
    expect(
      within(dialog).getByRole("checkbox", { name: /Menu Item 12/ }),
    ).toBeInTheDocument();
    // Archived catalog item (Menu Item 11) is not offered.
    expect(
      within(dialog).queryByRole("checkbox", { name: /Menu Item 11/ }),
    ).not.toBeInTheDocument();
  });

  it("excludes inactive/archived dining locations from the new-menu location choices", async () => {
    const user = userEvent.setup();
    renderWithRouter(<App />, { route: "/menus" });

    await user.click(screen.getByRole("button", { name: /Create Menu/ }));
    const dialog = screen.getByRole("dialog");
    const select = within(dialog).getByLabelText("Dining location");

    // Active location present.
    expect(
      within(select).getByRole("option", { name: "Dining Hall A" }),
    ).toBeInTheDocument();
    // Inactive (Dining Hall D) and archived (Dining Hall E) excluded.
    expect(
      within(select).queryByRole("option", { name: "Dining Hall D" }),
    ).not.toBeInTheDocument();
    expect(
      within(select).queryByRole("option", { name: "Dining Hall E" }),
    ).not.toBeInTheDocument();
  });

  it("still renders seeded menus with their managed location names", () => {
    renderWithRouter(<App />, { route: "/menus" });
    // Seeded menus resolve their location name from the managed records.
    expect(
      screen.getAllByRole("heading", { name: "Dining Hall A" }).length,
    ).toBeGreaterThan(0);
  });
});
