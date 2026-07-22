import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import App from "../App";
import { renderWithRouter } from "../test/renderWithRouter";

const overview = () => renderWithRouter(<App />, { route: "/menus" });

describe("Menus overview", () => {
  it("filters the list by status and clears back to the full list", async () => {
    const user = userEvent.setup();
    overview();

    // Draft menu visible initially.
    expect(
      screen.getByRole("button", { name: "Edit Dining Hall A Lunch menu" }),
    ).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Status"), "published");

    expect(
      screen.queryByRole("button", { name: "Edit Dining Hall A Lunch menu" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Edit Dining Hall A Breakfast menu" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Clear filters" }));

    expect(
      screen.getByRole("button", { name: "Edit Dining Hall A Lunch menu" }),
    ).toBeInTheDocument();
  });

  it("shows a filtered empty state with a clear action", async () => {
    const user = userEvent.setup();
    overview();

    // Location A has no dinner menu → filtering to A + Dinner yields nothing.
    await user.selectOptions(screen.getByLabelText("Dining location"), "loc-a");
    await user.selectOptions(screen.getByLabelText("Meal period"), "dinner");

    expect(
      screen.getByText("No menus match the current filters"),
    ).toBeInTheDocument();
  });

  it("navigates between dates", async () => {
    const user = userEvent.setup();
    overview();

    expect(
      screen.queryByRole("heading", { name: "Dining Hall E" }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Next day" }));

    expect(
      screen.getByRole("heading", { name: "Dining Hall E" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Today" }));

    expect(
      screen.queryByRole("heading", { name: "Dining Hall E" }),
    ).not.toBeInTheDocument();
  });

  it("publishes a draft menu locally", async () => {
    const user = userEvent.setup();
    overview();

    const publish = screen.getByRole("button", {
      name: "Publish Dining Hall A Lunch menu",
    });
    expect(publish).toBeEnabled();

    await user.click(publish);

    expect(
      screen.getByRole("button", { name: "Publish Dining Hall A Lunch menu" }),
    ).toBeDisabled();
  });

  it("marks a published menu as draft locally", async () => {
    const user = userEvent.setup();
    overview();

    const markDraft = screen.getByRole("button", {
      name: "Mark Dining Hall A Breakfast menu as draft",
    });
    expect(markDraft).toBeEnabled();

    await user.click(markDraft);

    expect(
      screen.getByRole("button", {
        name: "Mark Dining Hall A Breakfast menu as draft",
      }),
    ).toBeDisabled();
  });

  it("duplicates a menu into a session copy", async () => {
    const user = userEvent.setup();
    overview();

    expect(
      screen.getAllByRole("heading", { name: "Dining Hall C" }),
    ).toHaveLength(1);

    await user.click(
      screen.getByRole("button", {
        name: "Duplicate Dining Hall C Dinner menu",
      }),
    );

    expect(
      screen.getAllByRole("heading", { name: "Dining Hall C" }),
    ).toHaveLength(2);
  });

  it("deletes a menu after confirmation", async () => {
    const user = userEvent.setup();
    overview();

    expect(
      screen.getAllByRole("heading", { name: "Dining Hall D" }),
    ).toHaveLength(1);

    await user.click(
      screen.getByRole("button", { name: "Delete Dining Hall D Dinner menu" }),
    );
    // Confirm dialog "Delete" button (exact name distinguishes it from the card).
    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(
      screen.queryByRole("heading", { name: "Dining Hall D" }),
    ).not.toBeInTheDocument();
  });

  it("creates a menu and opens the editor", async () => {
    const user = userEvent.setup();
    overview();

    await user.click(screen.getByRole("button", { name: /Create Menu/ }));
    const dialog = screen.getByRole("dialog");
    await user.selectOptions(
      within(dialog).getByLabelText("Dining location"),
      "loc-e",
    );
    await user.click(
      within(dialog).getByRole("button", { name: /Create Menu/ }),
    );

    expect(
      screen.getByRole("heading", { name: "Menu details" }),
    ).toBeInTheDocument();
  });
});
