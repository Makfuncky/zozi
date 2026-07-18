import { expect, test } from "@playwright/test";

const ADMIN_USER = { username: "admin@zozi.com", password: "admin123" };

async function loginAsAdmin(page: import("@playwright/test").Page) {
  // Set the session flag BEFORE navigation (page.evaluate on about:blank throws
  // a SecurityError and would be swallowed, leaving the flag unset).
  await page.addInitScript(() => window.localStorage.setItem("zozi_has_session", "1"));
  const loginResponse = await page.request.post("/api/auth/login", {
    form: ADMIN_USER,
    failOnStatusCode: false,
  });
  expect(loginResponse.ok()).toBeTruthy();
  await page.request.get("/api/auth/me", { failOnStatusCode: false });
}

test.describe("Admin audit fixes", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("audit-logs page is wrapped in AdminLayout chrome", async ({ page }) => {
    await page.goto("/admin/audit-logs", { waitUntil: "domcontentloaded", timeout: 120_000 });

    // The bare stub had no AdminLayout; now the admin sidebar nav must render.
    await expect(
      page.getByRole("link", { name: /Command Center/i }).first(),
    ).toBeVisible({ timeout: 60_000 });

    // And the page heading is present (not the old raw <div>Audit logs content</div>).
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
    await loginAsAdmin(page);

    // The promotions page must load its flash-sales panel without routing errors.
    // Authenticate the page FIRST (it performs its own silent refresh) so the
    // refresh cookie is not consumed before the page loads — otherwise the page's
    // own silent refresh would send an already-used token and get bounced to login.
    await page.goto("/admin/promotions?section=flash-sales", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(
      page.getByRole("heading", { name: /Promotions/i }).first(),
    ).toBeVisible({ timeout: 30_000 });

    // Now verify the promotions API prefix resolves to the real backend route
    // (unauthenticated /admin requests are rejected with 401 before routing).
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
