import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("renders the admin application shell", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "PlateWise Admin" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Application shell running")).toBeInTheDocument();
  });
});
