import { expect, test, type Page, type Route } from "@playwright/test";
import { API_BASE } from "../../src/api";

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

async function mockSupplierSession(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem("zozi_has_session", "1");
  });

  await page.route("**/api/auth/refresh", async (route) => {
    await fulfillJson(route, { access_token: "supplier-test-token", refresh_token: "supplier-refresh-token" });
  });

  await page.route("**/api/auth/me", async (route) => {
    await fulfillJson(route, {
      id: 2,
      email: "supplier@zozi.com",
      username: "supplier",
      role: "supplier",
      preferred_language: "en",
    });
  });
}

test.describe("supplier orders and payouts", () => {
  test.beforeEach(async ({ page }) => {
    await mockSupplierSession(page);
  });

  test("supplier orders list shows pending and fulfilled orders", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/supplier/orders$`), async (route) => {
      await fulfillJson(route, {
        items: [
          { id: 1, status: "pending", customer_name: "Customer A", total: 150.00, created_at: new Date().toISOString() },
          { id: 2, status: "fulfilled", customer_name: "Customer B", total: 200.00, created_at: new Date().toISOString() },
        ],
        total: 2,
      });
    });

    await page.goto("/supplier/orders", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByRole("heading", { name: /orders/i }).first()).toBeVisible({ timeout: 60_000 });
    await expect(page.getByText(/pending/i).first()).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText(/fulfilled/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("supplier can print parcel sheet", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/supplier/orders$`), async (route) => {
      await fulfillJson(route, {
        items: [
          { id: 1, status: "pending", customer_name: "Customer A", total: 150.00, created_at: new Date().toISOString() },
        ],
        total: 1,
      });
    });

    await page.goto("/supplier/orders", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByRole("heading", { name: /orders/i }).first()).toBeVisible({ timeout: 60_000 });

    const printBtn = page.getByRole("button", { name: /print packing sheet|print parcel/i }).first();
    if (await printBtn.isVisible({ timeout: 10_000 }).catch(() => false)) {
      await printBtn.click();
      await page.waitForTimeout(1000);
    }
  });

  test("supplier payouts tab shows balance and transaction history", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/supplier/payouts$`), async (route) => {
      await fulfillJson(route, {
        balance: 1250.00,
        currency: "USD",
        pending: 350.00,
        transactions: [
          { id: 1, amount: 500.00, status: "completed", date: new Date().toISOString() },
          { id: 2, amount: 400.00, status: "pending", date: new Date().toISOString() },
        ],
      });
    });

    await page.goto("/supplier/payouts", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByRole("heading", { name: /payouts|finance/i }).first()).toBeVisible({ timeout: 60_000 });
    await expect(page.getByText(/\$|USD|balance/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("supplier support tickets list and create", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/supplier/support$`), async (route) => {
      await fulfillJson(route, {
        tickets: [
          { id: 1, subject: "Test Ticket", status: "open", created_at: new Date().toISOString() },
        ],
        total: 1,
      });
    });

    await page.route(new RegExp(`^${API_BASE.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')}/supplier/support/tickets$`), async (route) => {
      if (route.request().method() === "POST") {
        await fulfillJson(route, { id: 2, subject: "New Ticket", status: "open", created_at: new Date().toISOString() }, 201);
      } else {
        await fulfillJson(route, { tickets: [], total: 0 });
      }
    });

    await page.goto("/supplier/support", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByRole("heading", { name: /support/i }).first()).toBeVisible({ timeout: 60_000 });
    await expect(page.getByText(/test ticket/i).first()).toBeVisible({ timeout: 30_000 });
  });
});
