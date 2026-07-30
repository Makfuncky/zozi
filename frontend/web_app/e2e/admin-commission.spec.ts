/**
 * Admin Commission Management — Playwright E2E Tests
 *
 * Covers /admin/commission page: overview config, category rates,
 * and badge tiers.
 */
import { expect, test, type Page, type Route } from "@playwright/test";
import { bootstrapAdminSessionViaApi } from "./helpers/auth";

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function mockAdminSession(page: Page) {
  await page.context().clearCookies();
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.evaluate(() => window.localStorage.removeItem("zozi_has_session")).catch(() => undefined);

  for (const candidate of ["admin@zozi.com", "admin"]) {
    await bootstrapAdminSessionViaApi(page);

    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    await page.goto("/admin/commission", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const gate = page.getByRole("heading", { name: /Admin Access/i });
    if (!(await gate.isVisible().catch(() => false))) {
      await page.route("**/cart/**", async (r) => fulfillJson(r, []));
      await page.route("**/notifications**", async (r) => fulfillJson(r, []));
      await page.route("**/api/notifications**", async (r) => fulfillJson(r, []));
      return;
    }
  }

  await page.goto("/admin/login", { waitUntil: "domcontentloaded", timeout: 120_000 });
  const btn = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await btn.waitFor();
  const form = btn.locator("xpath=ancestor::form[1]");
  await form.locator("input:not([type='password']):visible").first().fill("admin@zozi.com");
  await form.locator("input[type='password']:visible").first().fill("admin123");
  await btn.click();
  await page.waitForTimeout(5000);
  await page.goto("/admin/commission", { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.route("**/cart/**", async (r) => fulfillJson(r, []));
  await page.route("**/notifications**", async (r) => fulfillJson(r, []));
  await page.route("**/api/notifications**", async (r) => fulfillJson(r, []));
}

test.describe("Admin Commission Management", () => {
  let rates: any[];
  let tiers: any[];

  test.beforeEach(async ({ page }) => {
    rates = [
      { id: 1, category_slug: "electronics", category_display_name: "Electronics", rate_percent: 0.08, is_active: true },
      { id: 2, category_slug: "fashion", category_display_name: "Fashion", rate_percent: 0.12, is_active: true },
    ];

    tiers = [
      { id: 1, badge_level: "bronze", commission_rate: 0.05, min_fulfilled_orders: 0, is_active: true },
      { id: 2, badge_level: "silver", commission_rate: 0.08, min_fulfilled_orders: 50, is_active: true },
    ];

    // Global config (commission.py router — /commission/global)
    await page.route("**/commission/global", async (route) => {
      if (route.request().method() === "GET") {
        await fulfillJson(route, {
          default_rate: 0.1,
          min_order: 50,
          max_cap: 1000,
          is_active: true,
        });
      } else {
        await route.continue();
      }
    });

    // Admin commission routes
    await page.route("**/admin/commission/**/rates", async (route) => {
      if (route.request().method() === "GET") {
        await fulfillJson(route, rates);
      } else {
        const body = route.request().postDataJSON();
        const newRate = {
          id: rates.length + 1,
          category_slug: body.category_slug,
          category_display_name: body.category_display_name,
          rate_percent: body.rate,
          is_active: body.is_active ?? true,
        };
        rates.push(newRate);
        await fulfillJson(route, newRate, 201);
      }
    });

    await page.route("**/admin/commission/**/badge-tiers", async (route) => {
      if (route.request().method() === "GET") {
        await fulfillJson(route, tiers);
      } else {
        const body = route.request().postDataJSON();
        const newTier = {
          id: tiers.length + 1,
          badge_level: body.badge_level,
          commission_rate: body.commission_rate,
          min_fulfilled_orders: body.min_fulfilled_orders ?? 0,
          is_active: body.is_active ?? true,
        };
        tiers.push(newTier);
        await fulfillJson(route, newTier, 201);
      }
    });

    // Suppliers list for overview
    await page.route("**/commission/suppliers**", async (route) => {
      await fulfillJson(route, {
        items: [
          { supplier_id: 101, business_name: "Mock Supply", current_rate: 0.1, total_earned: 450, order_count: 12 },
        ],
        total: 1, page: 1, page_size: 25, total_pages: 1,
      });
    });

    await mockAdminSession(page);
  });

  test("overview tab shows global config and summary cards", async ({ page }) => {
    await page.waitForTimeout(2000);
    await expect(page.getByText(/Commission Management/i)).toBeVisible();
    await expect(page.getByText(/Global Commission Configuration/i)).toBeVisible({ timeout: 5000 });
  });

  test("category rates tab lists rates and supports add", async ({ page }) => {
    await page.waitForTimeout(1500);
    await page.getByRole("tab", { name: /category rates/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByRole("button", { name: /add category rate/i })).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/Electronics/i)).toBeVisible();

    await page.getByRole("button", { name: /add category rate/i }).click();
    await expect(page.getByText(/Add Category Rate/i)).toBeVisible({ timeout: 5000 });

    await page.getByPlaceholder(/electronics/i).fill("home-garden");
    await page.getByPlaceholder(/Electronics/i).fill("Home & Garden");
    await page.locator('input[type="number"]').fill("0.07");
    await page.getByRole("button", { name: /save/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByText(/Home & Garden/i)).toBeVisible();
  });

  test("badge tiers tab lists tiers and supports add", async ({ page }) => {
    await page.waitForTimeout(1500);
    await page.getByRole("tab", { name: /badge tiers/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByRole("button", { name: /add badge tier/i })).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/bronze/i)).toBeVisible();

    await page.getByRole("button", { name: /add badge tier/i }).click();
    await expect(page.getByText(/Add Badge Tier/i)).toBeVisible({ timeout: 5000 });

    await page.getByPlaceholder(/bronze/i).fill("gold");
    await page.locator('input[type="number"]').first().fill("0.12");
    await page.getByRole("button", { name: /save/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByText(/gold/i)).toBeVisible();
  });
});

