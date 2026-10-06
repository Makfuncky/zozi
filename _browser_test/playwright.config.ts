import { defineConfig, devices } from "@playwright/test";

/** Identifies one run's evidence directory. */
const RUN_ID = process.env.RUN_ID || new Date().toISOString().replace(/[:.]/g, "-");

/**
 * Numeric env reader.
 *
 * Accepts plain digits ("30000") and underscore-separated digits ("30_000").
 * A bare `parseInt("30_000")` returns 30 because parseInt stops at the
 * underscore, which would silently collapse every timeout below.
 */
function envInt(name: string, fallback: number): number {
  const raw = process.env[name];
  if (raw === undefined || raw.trim() === "") return fallback;
  const parsed = Number.parseInt(raw.trim().replace(/_/g, ""), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export default defineConfig({
  testDir: "./tests",
  testMatch: /.*\.spec\.ts$/,
  // The suite mutates shared backend state (orders, finance ledgers, KYC
  // drafts), so tests must not race each other.
  fullyParallel: false,
  workers: envInt("PW_WORKERS", 1),
  timeout: envInt("PW_TIMEOUT", 120_000),
  retries: envInt("PW_RETRIES", 1),
  globalSetup: "./global-setup.ts",
  globalTeardown: "./global-teardown.ts",
  expect: {
    timeout: envInt("PW_EXPECT_TIMEOUT", 15_000),
  },
  use: {
    baseURL: process.env.WEB_BASE_URL || "http://127.0.0.1:3100",
    // Evidence mode is the point of this suite: capture every run, not just
    // failures. Set EVIDENCE=off to fall back to failure-only retention.
    screenshot: process.env.EVIDENCE === "off" ? "only-on-failure" : "on",
    video: process.env.EVIDENCE === "off" ? "retain-on-failure" : "on",
    trace: process.env.EVIDENCE === "off" ? "retain-on-failure" : "on",
    actionTimeout: envInt("PW_ACTION_TIMEOUT", 30_000),
    navigationTimeout: envInt("PW_NAV_TIMEOUT", 120_000),
  },
  reporter: [
    ["list"],
    ["html", { outputFolder: "reports/html", open: "never" }],
    ["json", { outputFile: "reports/run/results.json" }],
    ["junit", { outputFile: "reports/run/junit.xml" }],
  ],
  outputDir: `test-results/${RUN_ID}`,
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});