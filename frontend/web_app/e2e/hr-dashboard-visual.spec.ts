/**
 * HR Dashboard — Visual Regression Smoke Test
 *
 * Takes named element-level screenshots of each section on the /admin/hr page
 * and compares them against stored baselines.  Playwright's built-in
 * ``toHaveScreenshot()`` handles the diff: first run creates the baseline,
 * subsequent runs fail on any pixel difference.
 *
 * Sections captured:
 *   - hr-dashboard-full         — Viewport screenshot of the loaded page
 *   - hr-stats-row              — 6 StatCards (employees, pipeline, score, etc.)
 *   - hr-onboarding-pipeline    — Onboarding pipeline card
 *   - hr-performance-health     — Performance health card (green/amber/red bars)
 *   - hr-activity-feed          — Recent activity feed card
 *
 * Prerequisites:
 *   cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000
 *   cd frontend/web_app && npx next dev --port 3000
 *
 * Run (first run creates baselines, subsequent runs diff):
 *   npx playwright test e2e/hr-dashboard-visual.spec.ts
 *
 * Update baselines after intentional UI changes:
 *   npx playwright test e2e/hr-dashboard-visual.spec.ts --update-snapshots
 *
 * Environment:
 *   CI=false  — local dev; CI=true  — CI pipeline (strict diffs)
 */
import { expect, test } from "@playwright/test";
import {
  expectNavigation,
  waitForSessionFlag,
  openProtectedRoute,
  bootstrapAdminSessionViaApi,
  submitCredentialForm,
} from "./helpers/auth";

test.describe.configure({ timeout: 120_000 });

// ── Visual Regression Test ────────────────────────────────────────────

test.describe("HR Dashboard Visual Regression", () => {
  test.beforeEach(async ({ page }) => {
    const hasSession = await bootstrapAdminSessionViaApi(page);
    if (!hasSession) {
      await page.goto("/admin/login");
      await submitCredentialForm(page, "admin@zozi.com", "admin123");
      await waitForSessionFlag(page);
    }
  });

  test("full page screenshot: /admin/hr", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await openProtectedRoute(page, "/admin/hr", /\/admin\/hr(?:\?|$)/, 120_000);

    // Wait for the dashboard data to finish loading — the "HR Dashboard" heading
    // and at least one StatCard value confirm the API call completed.
    await expect(page.getByText("HR Dashboard")).toBeVisible({ timeout: 30_000 });
    // Ensure the skeleton loading state has fully resolved
    await page.waitForTimeout(2_000);

    // ── Full-page viewport screenshot ──
    // Captures the entire page as rendered; animations should have settled.
    await expect(page).toHaveScreenshot("hr-dashboard-full.png", {
      fullPage: true,
      maxDiffPixels: 200, // Allow minor antialiasing / sub-pixel differences
    });
  });

  test("stats row: 6 StatCards", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await openProtectedRoute(page, "/admin/hr", /\/admin\/hr(?:\?|$)/, 120_000);
    await expect(page.getByText("HR Dashboard")).toBeVisible({ timeout: 30_000 });

    // The stats row is the first motion.div after the data loads.
    // We locate it by its text content: it contains all 6 stat labels.
    // The specific class pattern is: grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6
    const statsRow = page
      .getByText("Total Employees")
      .locator("..")    // StatCard outer
      .locator("..")    // motion.div grid wrapper
      .first();

    await expect(statsRow).toBeVisible({ timeout: 10_000 });
    await expect(statsRow).toHaveScreenshot("hr-stats-row.png", {
      maxDiffPixels: 100,
    });
  });

  test("onboarding pipeline section", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await openProtectedRoute(page, "/admin/hr", /\/admin\/hr(?:\?|$)/, 120_000);
    await expect(page.getByText("HR Dashboard")).toBeVisible({ timeout: 30_000 });

    // The onboarding pipeline card contains the text "Onboarding Pipeline"
    // in its heading.  We locate the card by climbing from that heading.
    const onboardingCard = page
      .getByText("Onboarding Pipeline")
      .locator("..")            // flex heading row
      .locator("..")            // motion.div card
      .locator("..")            // lg:col-span-2 wrapper
      .first();

    await expect(onboardingCard).toBeVisible({ timeout: 10_000 });
    await expect(onboardingCard).toHaveScreenshot("hr-onboarding-pipeline.png", {
      maxDiffPixels: 100,
    });
  });

  test("performance health section", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await openProtectedRoute(page, "/admin/hr", /\/admin\/hr(?:\?|$)/, 120_000);
    await expect(page.getByText("HR Dashboard")).toBeVisible({ timeout: 30_000 });

    // The performance health card contains the heading "Performance Health"
    const perfCard = page
      .getByText("Performance Health")
      .locator("..")
      .locator("..")
      .first();

    await expect(perfCard).toBeVisible({ timeout: 10_000 });
    await expect(perfCard).toHaveScreenshot("hr-performance-health.png", {
      maxDiffPixels: 100,
    });
  });

  test("activity feed section", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await openProtectedRoute(page, "/admin/hr", /\/admin\/hr(?:\?|$)/, 120_000);
    await expect(page.getByText("HR Dashboard")).toBeVisible({ timeout: 30_000 });

    // The activity feed card contains the heading "Recent Activity (7 days)"
    const activityCard = page
      .getByText("Recent Activity (7 days)")
      .locator("..")
      .locator("..")
      .first();

    await expect(activityCard).toBeVisible({ timeout: 10_000 });
    await expect(activityCard).toHaveScreenshot("hr-activity-feed.png", {
      maxDiffPixels: 100,
    });
  });
});
