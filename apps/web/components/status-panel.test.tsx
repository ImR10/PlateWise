import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusPanel } from "./status-panel";

describe("StatusPanel", () => {
  it("shows a connected API", () => {
    render(
      <StatusPanel
        result={{
          connected: true,
          data: { service: "PlateWise API", status: "ok", environment: "test" },
        }}
      />,
    );

    expect(screen.getByText("API connected")).toBeInTheDocument();
    expect(screen.getByLabelText("Connected")).toBeInTheDocument();
  });

  it("shows an unavailable API", () => {
    render(<StatusPanel result={{ connected: false, message: "Offline" }} />);

    expect(screen.getByText("API unavailable")).toBeInTheDocument();
    expect(screen.getByText("Offline")).toBeInTheDocument();
  });
});
