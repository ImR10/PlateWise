import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";
import { renderWithRouter } from "./test/renderWithRouter";

describe("Dashboard content", () => {
  it("shows the University of Georgia identity", () => {
    renderWithRouter(<App />);

    expect(
      screen.getByRole("heading", { name: "PlateWise Admin" }),
    ).toBeInTheDocument();
    // Appears in the sidebar subtitle and the header university badge.
    expect(screen.getAllByText("University of Georgia").length).toBeGreaterThan(
      0,
    );
  });

  it("does not reference any other university", () => {
    renderWithRouter(<App />);

    expect(screen.queryByText(/Georgia Tech/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Emory/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Georgia State/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Georgia Southern/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Kennesaw/i)).not.toBeInTheDocument();
  });

  it("renders the prominent 'Are today's menus ready?' heading", () => {
    renderWithRouter(<App />);

    expect(
      screen.getByRole("heading", { name: "Are today's menus ready?" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Edit Today's Menus/ }),
    ).toBeInTheDocument();
  });

  it("renders all four meal services", () => {
    renderWithRouter(<App />);

    for (const meal of ["Breakfast", "Lunch", "Dinner", "Late Night"]) {
      expect(screen.getByText(meal)).toBeInTheDocument();
    }
  });

  it("renders the needs-attention items", () => {
    renderWithRouter(<App />);

    expect(screen.getByText("Missing Allergy Info")).toBeInTheDocument();
    expect(screen.getByText("Menu Not Published")).toBeInTheDocument();
    expect(screen.getByText("Missing Calories")).toBeInTheDocument();
    expect(screen.getByText("Duplicate Detected")).toBeInTheDocument();
  });

  it("renders exactly the four UGA dining locations", () => {
    renderWithRouter(<App />);

    expect(
      screen.getByRole("link", { name: /Bolton Dining Commons/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Snelling Dining Commons/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Village Summit/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Oglethorpe Dining Commons/ }),
    ).toBeInTheDocument();
  });

  it("renders the sidebar navigation", () => {
    renderWithRouter(<App />);

    const nav = screen.getByRole("navigation", { name: "Primary navigation" });
    for (const label of [
      "Dashboard",
      "Menus",
      "Dining Locations",
      "Food Catalog",
      "Activity",
      "Settings",
    ]) {
      expect(
        within(nav).getByRole("link", { name: label }),
      ).toBeInTheDocument();
    }
  });

  it("marks Dashboard as the active navigation item", () => {
    renderWithRouter(<App />);

    const nav = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(
      within(nav).getByRole("link", { name: "Dashboard" }),
    ).toHaveAttribute("aria-current", "page");
  });

  it("renders all quick actions", () => {
    renderWithRouter(<App />);

    for (const label of [
      "Create Menu",
      "Today's Menu",
      "Add Food",
      "Copy Previous",
      "Publish Menu",
    ]) {
      expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    }
  });

  it("renders upcoming menus and recent activity", () => {
    renderWithRouter(<App />);

    expect(screen.getByText("Tomorrow (Wed)")).toBeInTheDocument();
    // "John Doe" appears in both the sidebar profile and the activity feed.
    expect(screen.getAllByText("John Doe").length).toBeGreaterThan(0);
    expect(screen.getByText(/updated Chicken Alfredo/)).toBeInTheDocument();
  });
});
