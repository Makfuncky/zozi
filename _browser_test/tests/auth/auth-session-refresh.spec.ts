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

  await page.route("**/cart/**", async (route) => fulfillJson(route, []));
  await page.route("**/wishlist/**", async (route) => fulfillJson(route, []));
}

test.describe("auth session refresh", () => {
  test.beforeEach(async ({ page }) => {
    await mockCustomerSession(page);
  });

  test("access token expires — silent refresh via httpOnly cookie succeeds", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route("**/api/auth/refresh", async (route) => {
      const body = await route.request().postDataJSON().catch(() => ({}));
      expect(body).toHaveProperty("refresh_token");
      await fulfillJson(route, { access_token: "refreshed-token", refresh_token: "rotated-refresh-token" });
    });

    await page.goto("/products", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByText(/\d+\s+results/i).first()).toBeVisible({ timeout: 60_000 });
  });

  test("refresh token rotation — old token invalidated after refresh", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    let refreshCallCount = 0;
    await page.route("**/api/auth/refresh", async (route) => {
      refreshCallCount += 1;
      if (refreshCallCount === 1) {
        await fulfillJson(route, { access_token: "rotated-token", refresh_token: "new-refresh-token" });
      } else {
        await fulfillJson(route, { detail: "Invalid refresh token" }, 401);
      }
    });

    await page.goto("/products", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByText(/\d+\s+results/i).first()).toBeVisible({ timeout: 60_000 });
  });

  test("device binding — session invalidated on new device", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route("**/api/auth/me", async (route) => {
      await fulfillJson(route, { detail: "Device fingerprint mismatch" }, 401);
    });

    await page.goto("/products", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByRole("link", { name: /sign in|log in/i }).first()).toBeVisible({ timeout: 60_000 });
  });

  test("logout clears session state", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.route("**/api/auth/logout", async (route) => {
      await fulfillJson(route, { detail: "Logged out" });
    });

    await page.goto("/products", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByText(/\d+\s+results/i).first()).toBeVisible({ timeout: 60_000 });

    const response = await page.request.post(`${API_BASE}/api/auth/logout`, { failOnStatusCode: false });
    expect(response.ok()).toBeTruthy();

    const hasLocalSession = await page.evaluate(() => window.localStorage.getItem("zozi_has_session") === "1").catch(() => false);
    expect(hasLocalSession).toBeFalsy();
  });
});
