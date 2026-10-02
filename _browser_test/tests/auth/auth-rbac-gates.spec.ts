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
      permissions: ["catalog.view", "orders.create", "cart.view"],
    });
  });
}

async function mockAdminSession(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem("zozi_has_session", "1");
  });

  await page.route("**/api/auth/refresh", async (route) => {
    await fulfillJson(route, { access_token: "admin-test-token", refresh_token: "admin-refresh-token" });
  });

  await page.route("**/api/auth/me", async (route) => {
    await fulfillJson(route, {
      id: 1,
      email: "admin@zozi.com",
      username: "admin",
      role: "admin",
      preferred_language: "en",
      permissions: ["*"],
    });
  });
}

test.describe("auth rbac gates", () => {
  test("unauthorized feature access returns 403", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockCustomerSession(page);

    const response = await page.request.post(`${API_BASE}/admin/finance/ledger`, {
      failOnStatusCode: false,
      headers: { "Content-Type": "application/json" },
      data: { description: "Unauthorized post", amount: 100, currency: "USD" },
    });
    expect(response.status()).toBe(403);
  });

  test("authorized feature access returns 200", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockAdminSession(page);

    const response = await page.request.post(`${API_BASE}/admin/finance/ledger`, {
      failOnStatusCode: false,
      headers: { "Content-Type": "application/json" },
      data: { description: "Authorized post", amount: 100, currency: "USD" },
    });
    expect([200, 201]).toContain(response.status());
  });

  test("cross-tenant data isolation — country A cannot see country B data", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockAdminSession(page);

    const response = await page.request.get(`${API_BASE}/orders?country=SA`, {
      failOnStatusCode: false,
      headers: { "x-country-code": "AE" },
    });
    expect([200, 403]).toContain(response.status());
    if (response.status() === 200) {
      const body = await response.json().catch(() => ({}));
      const items = Array.isArray(body.items) ? body.items : [];
      expect(items.length).toBe(0);
    }
  });
});
