import path from "path";
import { defineConfig } from "@playwright/test";

const repoRoot = path.resolve(__dirname, "../..");
const backendDir = path.join(repoRoot, "backend");

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  workers: 2,
  timeout: 60_000,
  use: {
    baseURL: "http://127.0.0.1:8000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: `cd "${backendDir}" && python -m uvicorn main:app --host 0.0.0.0 --port 8000`,
      port: 8000,
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
  retries: process.env.CI ? 2 : 0,
});
