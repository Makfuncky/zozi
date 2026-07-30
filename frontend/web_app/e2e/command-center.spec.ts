import { expect, test } from "@playwright/test";
import { bootstrapAdminSessionViaApi } from "./helpers/auth";

test.describe("Command Center", () => {
  test.beforeEach(async ({ page }) => {
    // Set the session flag BEFORE any navigation (page.evaluate on about:blank
    // throws a SecurityError, so use addInitScript which runs on every document).
    await page.addInitScript(() => window.localStorage.setItem("zozi_has_session", "1"));
    await bootstrapAdminSessionViaApi(page);
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
  });

  const ZONES = [
    "Operational Overview",
    "Treasury",
    "Top Products",
    "Top Searches",
    "Departments",
    "Engine Room",
    "Market Intel",
  ];

  test("command center loads and renders all zones", async ({ page }) => {
    await page.goto("/admin/command-center", { waitUntil: "domcontentloaded", timeout: 180_000 });

    await expect(
      page.getByRole("heading", { name: "Command Center", exact: true }).first(),
    ).toBeVisible({ timeout: 60_000 });

    // The footer shows "LAST SYNC <time>" only after the /comprehensive feed loads.
    // If the feed fails the page instead renders a "TELEMETRY LINK LOST" banner.
    await expect(
      page.getByText(/SYNC|INITIALISING|TELEMETRY LINK LOST/).first(),
    ).toBeVisible({ timeout: 60_000 });

    for (const zone of ZONES) {
      await expect(page.getByRole("heading", { name: zone, level: 3 }).first()).toBeVisible({ timeout: 30_000 });
    }

    await page.screenshot({ path: "command-center-unified.png", fullPage: true });
  });

  test("command center data feed resolves (no telemetry-lost banner)", async ({ page }) => {
    await page.goto("/admin/command-center", { waitUntil: "domcontentloaded", timeout: 180_000 });

    await expect(
      page.getByRole("heading", { name: "Command Center", exact: true }).first(),
    ).toBeVisible({ timeout: 60_000 });

    // Successful data load replaces the "TELEMETRY LINK LOST" error banner state.
    await expect(
      page.getByText(/TELEMETRY LINK LOST/).first(),
    ).toBeHidden({ timeout: 60_000 });

    await expect(
      page.getByText(/SYNC|INITIALISING/).first(),
    ).toBeVisible({ timeout: 60_000 });

    for (const zone of ZONES) {
      await expect(page.getByRole("heading", { name: zone, level: 3 }).first()).toBeVisible({ timeout: 30_000 });
    }

    await page.screenshot({ path: "command-center-legacy.png", fullPage: true });
  });
});

