/**
 * HR Dashboard E2E Tests
 *
 * Exercises the admin HR dashboard page at /admin/hr:
 *  - Stats row (6 StatCards)
 *  - Onboarding pipeline section (overdue items / empty state)
 *  - Activity feed (events / empty state)
 *  - Performance health bars (green, amber, red)
 *
 * Prerequisites (start before running):
 *   cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000
 *   cd frontend/web_app && npx next dev --port 3000
 *
 * Run:
 *   cd frontend/web_app && npx playwright test e2e/hr-dashboard.spec.ts
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

// ── Tests ───────────────────────────────────────────────────────────────

test.describe("HR Dashboard Page", () => {
  test("API: /hr/dashboard returns expected shape", async ({ request }) => {
    // First login to get a valid token
    const loginResp = await request.post("http://127.0.0.1:8000/auth/login", {
      data: { email: "admin@zozi.com", password: "admin123" },
    });
    expect(loginResp.status()).toBe(200);
    const loginBody = await loginResp.json();
    const token = loginBody.access_token || loginBody.token;
    expect(token).toBeDefined();

    // Fetch dashboard
    const dashResp = await request.get("http://127.0.0.1:8000/hr/dashboard?days=7", {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(dashResp.status()).toBe(200);
    const body = await dashResp.json();

    // Verify the response shape
    expect(body).toHaveProperty("onboarding");
    expect(body.onboarding).toHaveProperty("stats");
    expect(body.onboarding.stats).toHaveProperty("active");
    expect(body.onboarding.stats).toHaveProperty("overdue");
    expect(body.onboarding.stats).toHaveProperty("completed");
    expect(body.onboarding.stats).toHaveProperty("cancelled");
    expect(body.onboarding).toHaveProperty("overdue_items");
    expect(Array.isArray(body.onboarding.overdue_items)).toBe(true);

    expect(body).toHaveProperty("performance");
    expect(body.performance).toHaveProperty("stats");
    expect(body.performance.stats).toHaveProperty("green");
    expect(body.performance.stats).toHaveProperty("amber");
    expect(body.performance.stats).toHaveProperty("red");
    expect(body.performance.stats).toHaveProperty("not_scored");
    expect(body.performance.stats).toHaveProperty("avg_score");
    expect(body.performance).toHaveProperty("top_performers");
    expect(body.performance).toHaveProperty("bottom_performers");

    expect(body).toHaveProperty("activity");
    expect(body.activity).toHaveProperty("total_events");
    expect(body.activity).toHaveProperty("action_breakdown");
    expect(body.activity).toHaveProperty("events");
    expect(Array.isArray(body.activity.events)).toBe(true);

    expect(body).toHaveProperty("employees");
    expect(body.employees).toHaveProperty("total");
    expect(body.employees).toHaveProperty("active");
    expect(body.employees).toHaveProperty("terminating");
    expect(body.employees).toHaveProperty("terminated");

    expect(body).toHaveProperty("dashboard_date");
  });

  test.describe("UI rendering (requires frontend server on :3000)", () => {
    test.beforeEach(async ({ page }) => {
      // Login via the UI form (not API) so the page's useAuth hook recognizes the session
      await page.goto("/admin/login");
      await submitCredentialForm(page, "admin@zozi.com", "admin123");
      await waitForSessionFlag(page, 60_000);
    });

    test("dashboard page renders stats row with 6 StatCard components", async ({ page }) => {
      test.slow();
      test.setTimeout(180_000);

      await openProtectedRoute(page, "/admin/hr", /\/admin\/hr(?:\?|$)/, 120_000);

      // Wait for the stats row to render (data loaded from backend)
      await expect(page.getByText("Total Employees").first()).toBeVisible({ timeout: 30_000 });

      // Verify StatCard labels are present (at least some of them — DB may have 0 values)
      const statLabels = [
        "Total Employees",
        "Active Pipeline",
        "Performance Score",
        "Green Performers",
        "Activity (7d)",
        "Terminating",
      ];
      for (const label of statLabels) {
        await expect(page.getByText(label).first()).toBeVisible({ timeout: 10_000 });
      }
    });

    test("dashboard page shows onboarding pipeline section", async ({ page }) => {
      test.slow();
      test.setTimeout(180_000);

      await openProtectedRoute(page, "/admin/hr", /\/admin\/hr(?:\?|$)/, 120_000);

      // Wait for onboarding section header to confirm it rendered
      await expect(page.getByText("Onboarding Pipeline")).toBeVisible({ timeout: 30_000 });
    });

    test("dashboard page shows activity feed section", async ({ page }) => {
      test.slow();
      test.setTimeout(180_000);

      await openProtectedRoute(page, "/admin/hr", /\/admin\/hr(?:\?|$)/, 120_000);

      // Wait for activity section header
      await expect(page.getByText("Recent Activity (7 days)")).toBeVisible({ timeout: 30_000 });

      // Verify the "Live" / "Offline" indicator badge is present
      const liveIndicator = page.getByText("Live");
      const offlineIndicator = page.getByText("Offline");
      const hasLive = await liveIndicator.isVisible().catch(() => false);
      const hasOffline = await offlineIndicator.isVisible().catch(() => false);
      expect(hasLive || hasOffline).toBe(true);

      // Verify the Refresh button is present
      await expect(page.getByText("Refresh")).toBeVisible();
    });

    test("dashboard page shows performance health section", async ({ page }) => {
      test.slow();
      test.setTimeout(180_000);

      await openProtectedRoute(page, "/admin/hr", /\/admin\/hr(?:\?|$)/, 120_000);

      // Wait for performance health header
      await expect(page.getByText("Performance Health")).toBeVisible({ timeout: 30_000 });

      // Health bars — check for at least one bar label
      const greenBar = page.getByText("Green (≥ 4.0)");
      const amberBar = page.getByText("Amber (2.5–4.0)");
      const redBar = page.getByText("Red (&lt; 2.5)");

      // At least one health bar should be visible
      const hasGreen = await greenBar.isVisible().catch(() => false);
      const hasAmber = await amberBar.isVisible().catch(() => false);
      const hasRed = await redBar.isVisible().catch(() => false);
      expect(hasGreen || hasAmber || hasRed).toBe(true);
    });
  });
});
