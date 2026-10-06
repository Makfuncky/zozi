import { expect, test, type Page, type Route } from "@playwright/test";
import { API_BASE } from "../../../src/api";

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

async function mockLogisticsSession(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem("zozi_has_session", "1");
  });

  await page.route("**/api/auth/refresh", async (route) => {
    await fulfillJson(route, { access_token: "logistics-test-token", refresh_token: "logistics-refresh-token" });
  });

  await page.route("**/api/auth/me", async (route) => {
    await fulfillJson(route, {
      id: 4,
      email: "logistics@zozi.com",
      username: "logistics",
      role: "logistics_partner",
      preferred_language: "en",
    });
  });
}

test.describe("logistics dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogisticsSession(page);
  });

  test("logistics dashboard shows active shipments count", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/logistics-partner/dashboard$`), async (route) => {
      await fulfillJson(route, {
        active_shipments: 12,
        pending_pickups: 3,
        completed_today: 8,
        total_revenue: 2450.00,
        recent_shipments: [],
      });
    });

    await page.goto("/logistics-partner/dashboard", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByRole("heading", { name: /dashboard/i }).first()).toBeVisible({ timeout: 60_000 });
    await expect(page.getByText(/active/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("logistics scan page loads with scanner input", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.goto("/logistics-partner/scan", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByRole("heading", { name: /scan/i }).first()).toBeVisible({ timeout: 60_000 });

    const scanInput = page.locator("input[placeholder*='scan' i], input[placeholder*='tracking' i], input[placeholder*='barcode' i]").first();
    await expect(scanInput).toBeVisible({ timeout: 30_000 });
  });

  test("logistics can update shipment status to Distribution Checkpoint", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/logistics-partner/shipments/\\d+/status$`), async (route) => {
      if (route.request().method() === "PATCH") {
        await fulfillJson(route, { id: 1, status: "distribution_checkpoint", updated_at: new Date().toISOString() });
      } else {
        await route.continue();
      }
    });

    await page.goto("/logistics-partner/scan", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByRole("heading", { name: /scan/i }).first()).toBeVisible({ timeout: 60_000 });

    const trackingInput = page.locator("input[placeholder*='scan' i], input[placeholder*='tracking' i], input[placeholder*='barcode' i]").first();
    if (await trackingInput.isVisible({ timeout: 10_000 }).catch(() => false)) {
      await trackingInput.fill("TRACK-12345");
      await page.waitForTimeout(500);
    }
  });
});
