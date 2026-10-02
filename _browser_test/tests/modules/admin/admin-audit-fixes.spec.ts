import { expect, test, type Page, type Route } from "@playwright/test";

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function mockAdminSession(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem("zozi_has_session", "1");
  });

  await page.route("**/api/auth/refresh**", async (route) => {
    await fulfillJson(route, { access_token: "admin-test-token" });
  });

  await page.route("**/api/auth/me**", async (route) => {
    await fulfillJson(route, {
      id: 1,
      email: "admin@zozi.com",
      username: "admin",
      role: "admin",
      permissions: ["analytics.view", "audit.read", "users.read"],
      preferred_language: "en",
    });
  });

  await page.route("**/admin/hierarchy/permissions", async (route) => {
    await fulfillJson(route, { matrix: null });
  });

  await page.route("**/cart/**", async (route) => fulfillJson(route, []));
  await page.route("**/notifications**", async (route) => fulfillJson(route, []));
  await page.route("**/api/notifications**", async (route) => fulfillJson(route, []));
}

test.describe("Admin audit fixes", () => {
  test.beforeEach(async ({ page }) => {
    await mockAdminSession(page);
  });

  test("audit-logs page is wrapped in AdminLayout chrome", async ({ page }) => {
    await page.goto("/admin/audit-logs", { waitUntil: "domcontentloaded", timeout: 120_000 });

    await expect(
      page.getByRole("link", { name: /Command Center/i }).first(),
    ).toBeVisible({ timeout: 60_000 });

    await expect(
      page.getByRole("heading", { name: "Audit Logs", exact: true }).first(),
    ).toBeVisible({ timeout: 30_000 });

    await page.screenshot({ path: "audit-logs-fixed.png", fullPage: true });
  });

  test("command-center renders after WebSocket client fix (no regression)", async ({ page }) => {
    await page.goto("/admin/command-center", { waitUntil: "domcontentloaded", timeout: 180_000 });

    await expect(
      page.getByRole("heading", { name: "Command Center", exact: true }).first(),
    ).toBeVisible({ timeout: 60_000 });

    await expect(
      page.getByText(/SYNC|INITIALISING|TELEMETRY LINK LOST/i).first(),
    ).toBeVisible({ timeout: 30_000 });

    await page.screenshot({ path: "command-center-fixed.png", fullPage: true });
  });

  test("promotions API uses the correct /admin/promotions prefix", async ({ page }) => {
    await mockAdminSession(page);

    await page.goto("/admin/promotions?section=flash-sales", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(
      page.getByRole("heading", { name: /Promotions/i }).first(),
    ).toBeVisible({ timeout: 30_000 });

    const refresh = await page.request.post("/auth/refresh", { failOnStatusCode: false });
    const token = refresh.ok() ? (await refresh.json()).access_token : null;
    const auth = token ? { Authorization: `Bearer ${token}` } : undefined;

    const good = await page.request.get("/admin/promotions/flash-sales", {
      headers: auth,
      failOnStatusCode: false,
    });
    expect(good.status()).toBe(200);
  });
});
