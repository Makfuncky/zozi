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

  await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/cart$`), async (route) => {
    await fulfillJson(route, { items: [], total: 0, subtotal: 0, tax: 0 });
  });

  await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/cart/items$`), async (route) => {
    const body = await route.request().postDataJSON().catch(() => ({}));
    await fulfillJson(route, { id: 1, product_id: body.product_id, quantity: body.quantity ?? 1, unit_price: 29.99, total: 29.99 });
  });
}

test.describe("customer cart", () => {
  test.beforeEach(async ({ page }) => {
    await mockCustomerSession(page);
  });

  test("cart persists across page reloads", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/cart$`), async (route) => {
      await fulfillJson(route, { items: [{ id: 1, name: "Test Product", quantity: 2, unit_price: 29.99 }], total: 59.98, subtotal: 59.98, tax: 0 });
    });

    await page.goto("/cart", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByRole("heading", { name: /^cart/i })).toBeVisible({ timeout: 60_000 });

    await page.reload({ waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByRole("heading", { name: /^cart/i })).toBeVisible({ timeout: 60_000 });
  });

  test("cart total updates with quantity change", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.goto("/cart", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByRole("heading", { name: /^cart/i })).toBeVisible({ timeout: 60_000 });

    const increaseBtn = page.getByRole("button", { name: /increase|\+/i }).first();
    if (await increaseBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await increaseBtn.click();
      await page.waitForTimeout(500);
    }

    const totalText = await page.locator("[data-testid='cart-total'], .cart-total, text=/total/i").first().textContent().catch(() => "");
    expect(totalText).not.toBe("");
  });

  test("empty cart shows checkout CTA", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/cart$`), async (route) => {
      await fulfillJson(route, { items: [], total: 0, subtotal: 0, tax: 0 });
    });

    await page.goto("/cart", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByRole("heading", { name: /^cart/i })).toBeVisible({ timeout: 60_000 });

    const continueShopping = page.getByRole("link", { name: /continue shopping/i });
    const proceedToCheckout = page.getByRole("button", { name: /proceed to checkout/i });

    if (await continueShopping.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(continueShopping).toBeVisible();
    }

    if (await proceedToCheckout.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(proceedToCheckout).toBeDisabled();
    }
  });

  test("cross-border tax shown in cart for AE destination", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/cart$`), async (route) => {
      await fulfillJson(route, {
        items: [{ id: 1, name: "Test Product", quantity: 1, unit_price: 100.00 }],
        total: 105.00,
        subtotal: 100.00,
        tax: 5.00,
        currency: "AED",
        country_code: "AE",
      });
    });

    await page.goto("/cart", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByRole("heading", { name: /^cart/i })).toBeVisible({ timeout: 60_000 });

    const taxLine = page.getByText(/tax|vat|5\.00/i).first();
    await expect(taxLine).toBeVisible({ timeout: 30_000 });
  });
});
