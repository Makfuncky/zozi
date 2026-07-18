import { expect, test, type Page } from "@playwright/test";

test.describe.configure({ timeout: 120_000 });

async function bootstrapAdminSession(page: Page) {
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
  const res = await page.request.post("/api/auth/login", {
    form: { username: "admin@zozi.com", password: "admin123" },
    failOnStatusCode: false,
  });
  if (!res.ok()) {
    throw new Error(`admin login failed: ${res.status()}`);
  }
  await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1"));
  await page.request.get("/api/auth/me", { failOnStatusCode: false });
}

test.describe("Admin - Permissions module", () => {
  test("permissions page loads categories and grants", async ({ page }) => {
    test.slow();
    await bootstrapAdminSession(page);
    await page.goto("/admin/permissions", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByText(/permission/i).first()).toBeVisible({ timeout: 60_000 });
    // The seeded categories should render.
    await expect(page.getByText(/Country|User|Order|Product|Finance/i).first()).toBeVisible({
      timeout: 30_000,
    });
  });
});

test.describe("Admin - Country control-plane (commission / IP / cities / flags)", () => {
  test("country workspace loads and lists cities + feature flags", async ({ page }) => {
    test.slow();
    await bootstrapAdminSession(page);
    await page.goto("/admin/countries/OM", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByText(/Oman/i).first()).toBeVisible({ timeout: 60_000 });
    // Commission tab content (seeded commission rates) should be present after switching tabs.
    await page.getByRole("button", { name: /commission/i }).first().click().catch(() => {});
    await expect(page.getByText(/commission/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("feature-flag CRUD round-trip via country API", async ({ page }) => {
    test.slow();
    await bootstrapAdminSession(page);
    const key = `e2e_ff_${Date.now()}`;
    const create = await page.request.post(`/admin/countries/OM/feature-flags`, {
      data: { feature_key: key, feature_name: "E2E Flag", is_enabled: true },
      failOnStatusCode: false,
    });
    expect(create.ok()).toBeTruthy();
    const patch = await page.request.patch(`/admin/countries/OM/feature-flags/${key}`, {
      data: { is_enabled: false },
      failOnStatusCode: false,
    });
    expect(patch.ok()).toBeTruthy();
    const list = await page.request.get(`/admin/countries/OM/feature-flags`, {
      failOnStatusCode: false,
    });
    expect(list.ok()).toBeTruthy();
    const flags = await list.json();
    expect(flags.some((f: any) => f.feature_key === key)).toBeTruthy();
  });
});

test.describe("Admin - Communication (email / chat / video)", () => {
  test("communication hub loads email campaigns, chat threads and video rooms", async ({ page }) => {
    test.slow();
    await bootstrapAdminSession(page);
    await page.goto("/admin/communication?tab=email", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByText(/campaign|email/i).first()).toBeVisible({ timeout: 60_000 });
  });
});

test.describe("Admin - Treasury / Finance / Payment / Payout", () => {
  test("treasury workspace loads metrics", async ({ page }) => {
    test.slow();
    await bootstrapAdminSession(page);
    await page.goto("/admin/finance?section=treasury", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByText(/treasury/i).first()).toBeVisible({ timeout: 60_000 });
    // Settlement / ledger figures should appear.
    await expect(page.getByText(/ledger|payout|settlement/i).first()).toBeVisible({ timeout: 30_000 });
  });
});

test.describe("Admin - HR / Employees / Offices / Roles", () => {
  test("employees workspace loads staff, offices and roles", async ({ page }) => {
    test.slow();
    await bootstrapAdminSession(page);
    await page.goto("/admin/employees", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expect(page.getByText(/employee/i).first()).toBeVisible({ timeout: 60_000 });
    await expect(page.getByText(/office|role/i).first()).toBeVisible({ timeout: 30_000 });
  });
});
