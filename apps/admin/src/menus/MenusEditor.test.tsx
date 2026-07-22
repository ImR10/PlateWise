import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import App from "../App";
import { renderWithRouter } from "../test/renderWithRouter";

const editor = (id = "menu-a-breakfast") =>
  renderWithRouter(<App />, { route: `/menus/${id}/edit` });

describe("Menu editor", () => {
  it("adds a station", async () => {
    const user = userEvent.setup();
    editor();

    expect(screen.queryByDisplayValue("Station C")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Add Station" }));
    expect(screen.getByDisplayValue("Station C")).toBeInTheDocument();
  });

  it("renames a station", async () => {
    const user = userEvent.setup();
    editor();

    const input = screen.getByDisplayValue("Station A");
    await user.clear(input);
    await user.type(input, "Grill Line");
    expect(screen.getByDisplayValue("Grill Line")).toBeInTheDocument();
  });

  it("reorders stations", async () => {
    const user = userEvent.setup();
    editor();

    const before = screen
      .getAllByLabelText("Station name")
      .map((el) => (el as HTMLInputElement).value);
    expect(before).toEqual(["Station A", "Station B"]);

    await user.click(
      screen.getByRole("button", { name: "Move Station A down" }),
    );

    const after = screen
      .getAllByLabelText("Station name")
      .map((el) => (el as HTMLInputElement).value);
    expect(after).toEqual(["Station B", "Station A"]);
  });

  it("adds an item from the catalog", async () => {
    const user = userEvent.setup();
    editor();

    await user.click(
      screen.getAllByRole("button", { name: "Add Food Item" })[0],
    );
    const dialog = screen.getByRole("dialog");
    await user.click(
      within(dialog).getByRole("checkbox", { name: /Menu Item 12/ }),
    );
    await user.click(
      within(dialog).getByRole("button", { name: /Add selected/ }),
    );

    expect(await screen.findByText("Menu Item 12")).toBeInTheDocument();
  });

  it("removes an item", async () => {
    const user = userEvent.setup();
    editor();

    expect(screen.getByText("Menu Item 01")).toBeInTheDocument();
    await user.click(
      screen.getByRole("button", { name: "Remove Menu Item 01" }),
    );
    expect(screen.queryByText("Menu Item 01")).not.toBeInTheDocument();
  });

  it("changes item availability", async () => {
    const user = userEvent.setup();
    editor();

    const group = screen.getByRole("group", {
      name: "Availability for Menu Item 01",
    });
    const limited = within(group).getByRole("button", { name: "Limited" });
    expect(limited).toHaveAttribute("aria-pressed", "false");

    await user.click(limited);

    expect(
      within(
        screen.getByRole("group", { name: "Availability for Menu Item 01" }),
      ).getByRole("button", { name: "Limited" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("moves an item within a station", async () => {
    const user = userEvent.setup();
    editor();

    // First item cannot move up initially.
    expect(
      screen.getByRole("button", { name: "Move Menu Item 01 up" }),
    ).toBeDisabled();

    await user.click(
      screen.getByRole("button", { name: "Move Menu Item 01 down" }),
    );

    expect(
      screen.getByRole("button", { name: "Move Menu Item 01 up" }),
    ).toBeEnabled();
  });

  it("shows an unsaved-changes indicator after an edit", async () => {
    const user = userEvent.setup();
    editor();

    expect(screen.queryByText("Unsaved changes")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Add Station" }));
    expect(screen.getByText("Unsaved changes")).toBeInTheDocument();
  });

  it("blocks publishing an invalid menu and shows an error summary", async () => {
    const user = userEvent.setup();
    editor("menu-b-breakfast");

    // Remove the only item so every station is empty.
    await user.click(
      screen.getByRole("button", { name: "Remove Menu Item 06" }),
    );
    await user.click(screen.getByRole("button", { name: "Publish" }));

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(/Add at least one item/);
    // Status is unchanged (still a draft, not published).
    expect(screen.queryByText("Published")).not.toBeInTheDocument();
  });

  it("publishes a valid menu and updates its status", async () => {
    const user = userEvent.setup();
    editor("menu-b-breakfast");

    expect(screen.getByText("Draft")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Publish" }));
    expect(screen.getByText("Published")).toBeInTheDocument();
  });
});
