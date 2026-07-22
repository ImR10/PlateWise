import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import App from "./App";
import { renderWithRouter } from "./test/renderWithRouter";

describe("Responsive navigation", () => {
  it("exposes a menu toggle that opens the collapsed sidebar drawer", async () => {
    const user = userEvent.setup();
    renderWithRouter(<App />);

    const toggle = screen.getByRole("button", {
      name: "Open navigation menu",
    });
    expect(toggle).toHaveAttribute("aria-controls", "primary-sidebar");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    // Only the in-drawer close button exists while collapsed (no backdrop).
    expect(screen.getAllByLabelText("Close navigation menu")).toHaveLength(1);

    await user.click(toggle);

    expect(toggle).toHaveAttribute("aria-expanded", "true");
    // Drawer close button + backdrop close button are both present now.
    expect(screen.getAllByLabelText("Close navigation menu")).toHaveLength(2);
  });

  it("closes the drawer when a navigation link is selected", async () => {
    const user = userEvent.setup();
    renderWithRouter(<App />);

    const toggle = screen.getByRole("button", {
      name: "Open navigation menu",
    });
    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");

    await user.click(screen.getByRole("link", { name: "Menus" }));

    // Navigated to the Menus placeholder and the drawer auto-closed.
    expect(
      screen.getByRole("heading", { name: "Menus", level: 2 }),
    ).toBeInTheDocument();
    expect(toggle).toHaveAttribute("aria-expanded", "false");
  });
});
