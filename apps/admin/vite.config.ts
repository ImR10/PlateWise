import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// PlateWise Admin is a standard browser-based single-page application.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 1420,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
  },
});
