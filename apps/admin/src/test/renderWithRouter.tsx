import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";

/** Render a component tree inside an in-memory router for tests. */
export function renderWithRouter(
  ui: ReactElement,
  { route = "/dashboard" }: { route?: string } = {},
) {
  return render(<MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>);
}
