import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import App from "../App";
import { renderWithRouter } from "../test/renderWithRouter";

const overview = () => renderWithRouter(<App />, { route: "/foods" });

describe("Food Catalog routing", () => {
  it("renders the overview at /foods", () => {
    overview();
    expect(
      screen.getByText(/Manage the catalog of food items/),
    ).toBeInTheDocument();
  });

  it("renders the create form at /foods/new", () => {
    renderWithRouter(<App />, { route: "/foods/new" });
    expect(
      screen.getByRole("heading", { name: "New food item" }),
    ).toBeInTheDocument();
  });

  it("renders the edit form for a valid id", () => {
    renderWithRouter(<App />, { route: "/foods/cat-01/edit" });
    expect(screen.getByDisplayValue("Menu Item 01")).toBeInTheDocument();
  });

  it("renders the preview for a valid id", () => {
    renderWithRouter(<App />, { route: "/foods/cat-01/preview" });
    expect(
      screen.getByText(/Preview only — changes are stored locally/),
    ).toBeInTheDocument();
    expect(screen.getByText("Allergens")).toBeInTheDocument();
  });

  it("shows a not-found state for an invalid id", () => {
    renderWithRouter(<App />, { route: "/foods/nope/edit" });
    expect(
      screen.getByRole("heading", { name: "Food item not found" }),
    ).toBeInTheDocument();
  });
});

describe("Food Catalog overview", () => {
  it("searches by name", async () => {
    const user = userEvent.setup();
    overview();
    await user.type(screen.getByLabelText("Search"), "Item 02");
    expect(
      screen.getByRole("heading", { name: "Menu Item 02" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Menu Item 01" }),
    ).not.toBeInTheDocument();
  });

  it("filters by category", async () => {
    const user = userEvent.setup();
    overview();
    await user.selectOptions(screen.getByLabelText("Category"), "Category D");
    // Menu Item 08 is Category D; Menu Item 01 is Category A.
    expect(
      screen.getByRole("heading", { name: "Menu Item 08" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Menu Item 01" }),
    ).not.toBeInTheDocument();
  });

  it("filters by dietary tag", async () => {
    const user = userEvent.setup();
    overview();
    await user.selectOptions(screen.getByLabelText("Dietary tag"), "Halal");
    expect(
      screen.getByRole("heading", { name: "Menu Item 03" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Menu Item 01" }),
    ).not.toBeInTheDocument();
  });

  it("filters by allergen", async () => {
    const user = userEvent.setup();
    overview();
    await user.selectOptions(screen.getByLabelText("Allergen"), "Fish");
    expect(
      screen.getByRole("heading", { name: "Menu Item 05" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Menu Item 01" }),
    ).not.toBeInTheDocument();
  });

  it("filters by status and clears filters", async () => {
    const user = userEvent.setup();
    overview();
    await user.selectOptions(screen.getByLabelText("Status"), "draft");
    // Menu Item 10 is the draft; Menu Item 01 is active.
    expect(
      screen.getByRole("heading", { name: "Menu Item 10" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Menu Item 01" }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(
      screen.getByRole("heading", { name: "Menu Item 01" }),
    ).toBeInTheDocument();
  });

  it("shows a filtered empty state", async () => {
    const user = userEvent.setup();
    overview();
    await user.type(screen.getByLabelText("Search"), "zzzzz");
    expect(
      screen.getByText("No food items match your filters"),
    ).toBeInTheDocument();
  });

  it("duplicates a food item", async () => {
    const user = userEvent.setup();
    overview();
    await user.click(
      screen.getByRole("button", { name: "Duplicate Menu Item 01" }),
    );
    expect(
      screen.getByRole("heading", { name: "Menu Item 01 (copy)" }),
    ).toBeInTheDocument();
  });

  it("archives a food item", async () => {
    const user = userEvent.setup();
    overview();
    await user.click(
      screen.getByRole("button", { name: "Archive Menu Item 01" }),
    );
    expect(
      screen.queryByRole("heading", { name: "Menu Item 01" }),
    ).not.toBeInTheDocument();
  });

  it("restores an archived food item", async () => {
    const user = userEvent.setup();
    overview();
    await user.click(screen.getByLabelText("Show archived items"));
    await user.click(
      screen.getByRole("button", { name: "Restore Menu Item 11" }),
    );
    expect(
      screen.getByRole("button", { name: "Archive Menu Item 11" }),
    ).toBeInTheDocument();
  });

  it("deletes a food item after confirmation", async () => {
    const user = userEvent.setup();
    overview();
    await user.selectOptions(screen.getByLabelText("Status"), "draft");
    await user.click(
      screen.getByRole("button", { name: "Delete Menu Item 10" }),
    );
    await user.click(screen.getByRole("button", { name: "Delete" }));
    expect(
      screen.queryByRole("heading", { name: "Menu Item 10" }),
    ).not.toBeInTheDocument();
  });

  it("creates a food item and shows it in the list", async () => {
    const user = userEvent.setup();
    overview();
    await user.click(screen.getByRole("button", { name: "Create Food Item" }));
    await user.type(screen.getByLabelText("Food-item name"), "Menu Item 13");
    await user.click(screen.getByRole("button", { name: "Save Draft" }));
    expect(
      screen.getByRole("heading", { name: "Menu Item 13" }),
    ).toBeInTheDocument();
  });
});

describe("Food Catalog editor", () => {
  const editItem = () =>
    renderWithRouter(<App />, { route: "/foods/cat-01/edit" });

  it("edits the name", async () => {
    const user = userEvent.setup();
    editItem();
    const name = screen.getByLabelText("Food-item name");
    await user.clear(name);
    await user.type(name, "Menu Item 13");
    expect(screen.getByDisplayValue("Menu Item 13")).toBeInTheDocument();
  });

  it("changes dietary tags", async () => {
    const user = userEvent.setup();
    editItem();
    const vegan = screen.getByRole("checkbox", { name: "Vegan" });
    expect(vegan).not.toBeChecked();
    await user.click(vegan);
    expect(screen.getByRole("checkbox", { name: "Vegan" })).toBeChecked();
  });

  it("changes allergens", async () => {
    const user = userEvent.setup();
    editItem();
    const soy = screen.getByRole("checkbox", { name: "Soy" });
    expect(soy).not.toBeChecked();
    await user.click(soy);
    expect(screen.getByRole("checkbox", { name: "Soy" })).toBeChecked();
  });

  it("changes default availability", async () => {
    const user = userEvent.setup();
    editItem();
    await user.selectOptions(
      screen.getByLabelText("Default availability"),
      "limited",
    );
    expect(screen.getByLabelText("Default availability")).toHaveValue(
      "limited",
    );
  });

  it("blocks activation when the name is missing", async () => {
    const user = userEvent.setup();
    renderWithRouter(<App />, { route: "/foods/new" });
    await user.click(screen.getByRole("button", { name: "Activate" }));
    expect(screen.getByRole("alert")).toHaveTextContent(
      /Enter a food-item name/,
    );
  });

  it("activates a valid food item", async () => {
    const user = userEvent.setup();
    renderWithRouter(<App />, { route: "/foods/cat-10/edit" });
    expect(screen.getByLabelText("Status")).toHaveValue("draft");
    await user.click(screen.getByRole("button", { name: "Activate" }));
    expect(screen.getByLabelText("Status")).toHaveValue("active");
  });
});

describe("Food Catalog preview", () => {
  const previewItem = () =>
    renderWithRouter(<App />, { route: "/foods/cat-10/preview" });

  it("hides internal notes", () => {
    previewItem();
    // cat-10 has an internal note that must not appear in the student preview.
    expect(
      screen.queryByText(/Awaiting allergen review/),
    ).not.toBeInTheDocument();
  });

  it("shows dietary tags and allergens", () => {
    renderWithRouter(<App />, { route: "/foods/cat-01/preview" });
    expect(screen.getByText("Dietary tags")).toBeInTheDocument();
    expect(screen.getByText("Allergens")).toBeInTheDocument();
    expect(screen.getByText("Vegetarian")).toBeInTheDocument();
  });

  it("toggles desktop and mobile preview", async () => {
    const user = userEvent.setup();
    previewItem();
    expect(
      screen.getByRole("button", { name: "Desktop Preview" }),
    ).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: "Mobile Preview" }));
    expect(
      screen.getByRole("button", { name: "Mobile Preview" }),
    ).toHaveAttribute("aria-pressed", "true");
  });
});
