import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import App from "../App";
import { renderWithRouter } from "../test/renderWithRouter";

const analysis = () => renderWithRouter(<App />, { route: "/analysis" });

/** Read a summary MetricCard's value by its title (scoped to the summary region). */
function metricValue(title: string): string {
  const section = screen.getByRole("region", { name: "Summary metrics" });
  const card = within(section)
    .getByText(title)
    .closest(".admin-card") as HTMLElement;
  return within(card).getByText((_, el) =>
    (el?.className ?? "").includes("text-h1"),
  ).textContent as string;
}

describe("Analysis routing", () => {
  it("renders at /analysis with the mock-data notice", () => {
    analysis();
    expect(screen.getByText(/Analysis preview/)).toBeInTheDocument();
    expect(
      screen.getByText(/currently uses mock and estimated data/),
    ).toBeInTheDocument();
  });

  it("is reachable from the sidebar", () => {
    analysis();
    const nav = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(
      within(nav).getByRole("link", { name: "Analysis" }),
    ).toBeInTheDocument();
  });
});

describe("Analysis summary metrics", () => {
  it("renders default totals and the derived top-demand item", () => {
    analysis();
    expect(
      Number(metricValue("Total recommendations").replace(/,/g, "")),
    ).toBeGreaterThan(0);
    expect(metricValue("Top-demand food item")).toBe("Menu Item 01");
    expect(metricValue("Highest-demand location")).toBe("Dining Hall A");
  });

  it("renders an estimated selection rate as a percentage", () => {
    analysis();
    expect(metricValue("Estimated selection rate")).toMatch(/^\d+%$/);
  });

  it("shows estimated indicators and comparison values", () => {
    analysis();
    expect(screen.getAllByText("Estimated").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/vs previous period/).length).toBeGreaterThan(0);
  });
});

describe("Analysis honesty", () => {
  it("uses estimated language and never claims verified consumption/inventory", () => {
    analysis();
    expect(screen.getAllByText("Estimated").length).toBeGreaterThan(0);
    expect(screen.queryByText(/verified waste/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/confirmed food consumed/i),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/exact servings taken/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/confirmed stock remaining/i),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(/actual inventory used/i),
    ).not.toBeInTheDocument();
  });

  it("renders a disabled export control with an explanation", () => {
    analysis();
    expect(screen.getByRole("button", { name: /Export/ })).toBeDisabled();
    expect(
      screen.getAllByText(/Available after analytics integration/).length,
    ).toBeGreaterThan(0);
  });
});

describe("Analysis filters", () => {
  it("date range updates metrics (last-30 has more recommendations than last-7)", async () => {
    const user = userEvent.setup();
    analysis();
    const before = Number(
      metricValue("Total recommendations").replace(/,/g, ""),
    );
    await user.selectOptions(screen.getByLabelText("Date range"), "last-30");
    const after = Number(
      metricValue("Total recommendations").replace(/,/g, ""),
    );
    expect(after).toBeGreaterThan(before);
  });

  it("location filter updates the top-demand item", async () => {
    const user = userEvent.setup();
    analysis();
    await user.selectOptions(screen.getByLabelText("Dining location"), "loc-d");
    expect(metricValue("Top-demand food item")).toBe("Menu Item 07");
  });

  it("meal-period filter updates the top-demand item", async () => {
    const user = userEvent.setup();
    analysis();
    await user.selectOptions(screen.getByLabelText("Meal period"), "breakfast");
    expect(metricValue("Top-demand food item")).toBe("Menu Item 02");
  });

  it("station filter updates the top-demand item", async () => {
    const user = userEvent.setup();
    analysis();
    await user.selectOptions(screen.getByLabelText("Station"), "stn-b");
    expect(metricValue("Top-demand food item")).toBe("Menu Item 02");
  });

  it("category filter updates the top-demand item", async () => {
    const user = userEvent.setup();
    analysis();
    await user.selectOptions(
      screen.getByLabelText("Food category"),
      "Category D",
    );
    expect(metricValue("Top-demand food item")).toBe("Menu Item 07");
  });

  it("comparison-period change removes comparison values", async () => {
    const user = userEvent.setup();
    analysis();
    expect(screen.getAllByText(/vs previous period/).length).toBeGreaterThan(0);
    await user.selectOptions(
      screen.getByLabelText("Comparison period"),
      "none",
    );
    expect(screen.queryByText(/vs previous period/)).not.toBeInTheDocument();
  });

  it("clears filters back to defaults", async () => {
    const user = userEvent.setup();
    analysis();
    await user.selectOptions(screen.getByLabelText("Dining location"), "loc-d");
    expect(metricValue("Top-demand food item")).toBe("Menu Item 07");
    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(metricValue("Top-demand food item")).toBe("Menu Item 01");
  });

  it("shows a no-results empty state for a filter combination with no data", async () => {
    const user = userEvent.setup();
    analysis();
    // Dining Hall E has no dinner events in the mock model.
    await user.selectOptions(screen.getByLabelText("Dining location"), "loc-e");
    await user.selectOptions(screen.getByLabelText("Meal period"), "dinner");
    expect(
      screen.getByText("No analytics match these filters"),
    ).toBeInTheDocument();
  });

  it("reveals custom start/end date inputs", async () => {
    const user = userEvent.setup();
    analysis();
    expect(screen.queryByLabelText("Start date")).not.toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Date range"), "custom");
    expect(screen.getByLabelText("Start date")).toBeInTheDocument();
    expect(screen.getByLabelText("End date")).toBeInTheDocument();
  });
});

describe("Analysis recommendation demand", () => {
  it("renders the ranked most-recommended items with Menu Item 01 first", () => {
    analysis();
    const chart = screen
      .getByRole("heading", { name: "Most recommended items" })
      .closest(".admin-card") as HTMLElement;
    const firstRowHeader = within(chart).getAllByRole("rowheader")[0];
    expect(firstRowHeader).toHaveTextContent("Menu Item 01");
  });
});

describe("Analysis estimated consumption", () => {
  it("uses estimated wording and not confirmed-consumption wording", () => {
    analysis();
    expect(screen.getAllByText(/estimated selections/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText(/not confirmed consumption/i).length,
    ).toBeGreaterThan(0);
  });
});

describe("Analysis selection-rate table", () => {
  it("sorts when a column header is activated", async () => {
    const user = userEvent.setup();
    analysis();
    const recBtn = screen.getByRole("button", { name: "Recommendations" });
    expect(recBtn.closest("th")).toHaveAttribute("aria-sort", "descending");
    await user.click(recBtn);
    expect(
      screen.getByRole("button", { name: "Recommendations" }).closest("th"),
    ).toHaveAttribute("aria-sort", "ascending");
  });

  it("distinguishes low-volume items under a narrow range", async () => {
    const user = userEvent.setup();
    analysis();
    await user.selectOptions(screen.getByLabelText("Date range"), "today");
    expect(screen.getAllByText("Low volume").length).toBeGreaterThan(0);
  });
});

describe("Analysis operational signals", () => {
  it("renders shortage and overproduction risk signals with advisory language", () => {
    analysis();
    expect(
      screen.getAllByRole("heading", { name: "Possible shortage risk" }).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByRole("heading", { name: "Possible overproduction risk" })
        .length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Suggested review:/).length).toBeGreaterThan(0);
  });

  it("filters signals by severity", async () => {
    const user = userEvent.setup();
    analysis();
    expect(
      screen.getAllByRole("heading", { name: "Stable demand" }).length,
    ).toBeGreaterThan(0);
    await user.selectOptions(
      screen.getByLabelText("Filter signals by severity"),
      "risk",
    );
    expect(
      screen.queryByRole("heading", { name: "Stable demand" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getAllByRole("heading", { name: "Possible shortage risk" }).length,
    ).toBeGreaterThan(0);
  });
});

describe("Analysis data-source panel", () => {
  it("renders mock and disconnected/integration statuses with explanations", () => {
    analysis();
    expect(screen.getByText("Data sources & quality")).toBeInTheDocument();
    expect(screen.getAllByText("Mock data").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Not connected").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Integration required").length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText("Backend required").length).toBeGreaterThan(0);
    expect(screen.getByText(/Measured waste analytics/)).toBeInTheDocument();
  });
});
