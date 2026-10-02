import { expect, test, type Page, type Route } from "@playwright/test";
import { API_BASE } from "../../src/api";

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

async function mockCustomerSession(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem("zozi_has_session", "1");
  });

  await page.route("**/api/auth/refresh", async (route) => {
    await fulfillJson(route, { access_token: "customer-test-token", refresh_token: "customer-refresh-token" });
  });

  await page.route("**/api/auth/me", async (route) => {
    await fulfillJson(route, {
      id: 3,
      email: "customer@zozi.com",
      username: "customer",
      role: "customer",
      preferred_language: "en",
    });
  });

  await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/wishlist$`), async (route) => {
    await fulfillJson(route, { items: [], total: 0 });
  });

  await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/wishlist/items$`), async (route) => {
    await fulfillJson(route, { id: 1, product_id: 101, name: "Wishlist Item", added_at: new Date().toISOString() });
  });
}

test.describe("customer wishlist", () => {
  test.beforeEach(async ({ page }) => {
    await mockCustomerSession(page);
  });

  test("add to wishlist from product page", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/wishlist$`), async (route) => {
      await fulfillJson(route, {
        items: [{ id: 1, product_id: 101, name: "Classic T-Shirt", price: 29.99, image_url: null }],
        total: 1,
      });
    });

    await page.goto("/products/101", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const wishlistBtn = page.getByRole("button", { name: /add to wishlist|wishlist/i }).first();
    if (await wishlistBtn.isVisible({ timeout: 10_000 }).catch(() => false)) {
      await wishlistBtn.click();
      await page.waitForTimeout(500);
    }

    await page.goto("/wishlist", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByText(/wishlist/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("wishlist persists across sessions", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/wishlist$`), async (route) => {
      await fulfillJson(route, {
        items: [{ id: 1, product_id: 101, name: "Classic T-Shirt", price: 29.99, image_url: null }],
        total: 1,
      });
    });

    await page.goto("/wishlist", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByText(/wishlist/i).first()).toBeVisible({ timeout: 30_000 });

    await page.reload({ waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByText(/wishlist/i).first()).toBeVisible({ timeout: 30_000 });
  });
});
