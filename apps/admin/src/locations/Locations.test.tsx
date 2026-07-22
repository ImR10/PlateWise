import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import App from "../App";
import { renderWithRouter } from "../test/renderWithRouter";

const overview = () => renderWithRouter(<App />, { route: "/locations" });

describe("Dining Locations routing", () => {
  it("renders the overview at /locations", () => {
    overview();
    expect(
      screen.getByText(/Manage dining locations, their service configuration/),
    ).toBeInTheDocument();
  });

  it("renders the create form at /locations/new", () => {
    renderWithRouter(<App />, { route: "/locations/new" });
    expect(
      screen.getByRole("heading", { name: "New dining location" }),
    ).toBeInTheDocument();
  });

  it("renders the edit form for a valid id", () => {
    renderWithRouter(<App />, { route: "/locations/loc-a/edit" });
    expect(screen.getByDisplayValue("Dining Hall A")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Basic details" }),
    ).toBeInTheDocument();
  });

  it("renders the preview for a valid id", () => {
    renderWithRouter(<App />, { route: "/locations/loc-a/preview" });
    expect(
      screen.getByText(/Preview only — changes are stored locally/),
    ).toBeInTheDocument();
    expect(screen.getByText("Operating hours")).toBeInTheDocument();
  });

  it("shows a not-found state for an invalid id", () => {
    renderWithRouter(<App />, { route: "/locations/nope/edit" });
    expect(
      screen.getByRole("heading", { name: "Dining location not found" }),
    ).toBeInTheDocument();
  });
});

describe("Dining Locations overview", () => {
  it("searches by name", async () => {
    const user = userEvent.setup();
    overview();

    expect(
      screen.getByRole("heading", { name: "Dining Hall A" }),
    ).toBeInTheDocument();
    await user.type(screen.getByLabelText("Search"), "Hall B");
    expect(
      screen.queryByRole("heading", { name: "Dining Hall A" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Dining Hall B" }),
    ).toBeInTheDocument();
  });

  it("filters by status and clears filters", async () => {
    const user = userEvent.setup();
    overview();

    await user.selectOptions(screen.getByLabelText("Status"), "draft");
    expect(
      screen.queryByRole("heading", { name: "Dining Hall A" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Dining Hall C" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(
      screen.getByRole("heading", { name: "Dining Hall A" }),
    ).toBeInTheDocument();
  });

  it("shows a filtered empty state", async () => {
    const user = userEvent.setup();
    overview();
    await user.type(screen.getByLabelText("Search"), "zzzzz");
    expect(
      screen.getByText("No dining locations match your filters"),
    ).toBeInTheDocument();
  });

  it("reveals archived locations via the toggle", async () => {
    const user = userEvent.setup();
    overview();

    expect(
      screen.queryByRole("heading", { name: "Dining Hall E" }),
    ).not.toBeInTheDocument();
    await user.click(screen.getByLabelText("Show archived locations"));
    expect(
      screen.getByRole("heading", { name: "Dining Hall E" }),
    ).toBeInTheDocument();
  });

  it("duplicates a location", async () => {
    const user = userEvent.setup();
    overview();
    await user.click(
      screen.getByRole("button", { name: "Duplicate Dining Hall A" }),
    );
    expect(
      screen.getByRole("heading", { name: "Dining Hall A (copy)" }),
    ).toBeInTheDocument();
  });

  it("archives a location", async () => {
    const user = userEvent.setup();
    overview();
    await user.click(
      screen.getByRole("button", { name: "Archive Dining Hall A" }),
    );
    expect(
      screen.queryByRole("heading", { name: "Dining Hall A" }),
    ).not.toBeInTheDocument();
  });

  it("restores an archived location", async () => {
    const user = userEvent.setup();
    overview();
    await user.click(screen.getByLabelText("Show archived locations"));
    await user.click(
      screen.getByRole("button", { name: "Restore Dining Hall E" }),
    );
    expect(
      screen.getByRole("button", { name: "Archive Dining Hall E" }),
    ).toBeInTheDocument();
  });

  it("deletes a location after confirmation", async () => {
    const user = userEvent.setup();
    overview();
    await user.click(
      screen.getByRole("button", { name: "Delete Dining Hall C" }),
    );
    await user.click(screen.getByRole("button", { name: "Delete" }));
    expect(
      screen.queryByRole("heading", { name: "Dining Hall C" }),
    ).not.toBeInTheDocument();
  });

  it("creates a location and shows it in the list", async () => {
    const user = userEvent.setup();
    overview();
    await user.click(
      screen.getByRole("button", { name: "Create Dining Location" }),
    );
    await user.type(screen.getByLabelText("Location name"), "Dining Hall F");
    await user.click(screen.getByRole("button", { name: "Save Draft" }));
    expect(
      screen.getByRole("heading", { name: "Dining Hall F" }),
    ).toBeInTheDocument();
  });
});

describe("Dining Locations editor", () => {
  const editA = () =>
    renderWithRouter(<App />, { route: "/locations/loc-a/edit" });

  it("edits basic details", async () => {
    const user = userEvent.setup();
    editA();
    const name = screen.getByLabelText("Location name");
    await user.clear(name);
    await user.type(name, "Dining Hall F");
    expect(screen.getByDisplayValue("Dining Hall F")).toBeInTheDocument();
  });

  it("adds a station", async () => {
    const user = userEvent.setup();
    editA();
    expect(screen.queryByDisplayValue("Station D")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Add Station" }));
    expect(screen.getByDisplayValue("Station D")).toBeInTheDocument();
  });

  it("renames a station", async () => {
    const user = userEvent.setup();
    editA();
    const input = screen.getByDisplayValue("Station A");
    await user.clear(input);
    await user.type(input, "Grill Line");
    expect(screen.getByDisplayValue("Grill Line")).toBeInTheDocument();
  });

  it("reorders stations", async () => {
    const user = userEvent.setup();
    editA();
    const before = screen
      .getAllByLabelText("Station name")
      .map((el) => (el as HTMLInputElement).value);
    expect(before).toEqual(["Station A", "Station B", "Station C"]);
    await user.click(
      screen.getByRole("button", { name: "Move Station A down" }),
    );
    const after = screen
      .getAllByLabelText("Station name")
      .map((el) => (el as HTMLInputElement).value);
    expect(after).toEqual(["Station B", "Station A", "Station C"]);
  });

  it("removes a station after confirmation", async () => {
    const user = userEvent.setup();
    editA();
    await user.click(screen.getByRole("button", { name: "Remove Station C" }));
    await user.click(screen.getByRole("button", { name: "Remove" }));
    expect(screen.queryByDisplayValue("Station C")).not.toBeInTheDocument();
  });

  it("edits operating hours", async () => {
    editA();
    const monday = screen.getByLabelText("Monday opening time");
    fireEvent.change(monday, { target: { value: "08:30" } });
    expect(screen.getByLabelText("Monday opening time")).toHaveValue("08:30");
  });

  it("blocks activation when required fields are missing", async () => {
    const user = userEvent.setup();
    renderWithRouter(<App />, { route: "/locations/new" });
    await user.click(screen.getByRole("button", { name: "Activate" }));
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(/Enter a location name/);
  });

  it("activates a valid location", async () => {
    const user = userEvent.setup();
    renderWithRouter(<App />, { route: "/locations/loc-c/edit" });
    expect(screen.getByLabelText("Status")).toHaveValue("draft");
    await user.click(screen.getByRole("button", { name: "Activate" }));
    expect(screen.getByLabelText("Status")).toHaveValue("active");
  });
});

describe("Dining Locations preview", () => {
  const previewA = () =>
    renderWithRouter(<App />, { route: "/locations/loc-a/preview" });

  it("hides internal notes and inactive stations", () => {
    previewA();
    expect(screen.queryByText(/Primary location/)).not.toBeInTheDocument();
    // Station C is inactive → not shown to students.
    expect(screen.queryByText("Station C")).not.toBeInTheDocument();
  });

  it("shows hours and active stations", () => {
    previewA();
    expect(screen.getByText("Operating hours")).toBeInTheDocument();
    expect(screen.getByText("Station A")).toBeInTheDocument();
  });

  it("toggles desktop and mobile preview", async () => {
    const user = userEvent.setup();
    previewA();
    expect(
      screen.getByRole("button", { name: "Desktop Preview" }),
    ).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: "Mobile Preview" }));
    expect(
      screen.getByRole("button", { name: "Mobile Preview" }),
    ).toHaveAttribute("aria-pressed", "true");
  });
});
