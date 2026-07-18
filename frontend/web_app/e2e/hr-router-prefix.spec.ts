import { expect, test } from "@playwright/test";

/**
 * Verifies the HR router-prefix fix: employee sub-tabs previously called
 * `/admin/hr/...` which has no backend route. The HR router is mounted at
 * `/hr` (backend `routers/hr.py`), so the correct, reachable path is `/hr/...`.
 * This spec also confirms HSE / Alumni tabs render gracefully even though
 * their backend GET endpoints are not yet implemented (tracked separately).
 */
test.describe("HR router-prefix fix", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => window.localStorage.setItem("zozi_has_session", "1"));
    const loginResponse = await page.request.post("/api/auth/login", {
      form: { username: "admin@zozi.com", password: "admin123" },
      failOnStatusCode: false,
    });
    expect(loginResponse.ok()).toBeTruthy();
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
  });

  test("disciplinary & offboarding tabs call /hr/ (not /admin/hr/) and resolve", async ({ page }) => {
    test.slow();
    const hrRequests: string[] = [];
    const badRequests: string[] = [];
    page.on("request", (req) => {
      const url = req.url();
      if (url.includes("/hr/")) hrRequests.push(url);
      if (url.includes("/admin/hr/")) badRequests.push(url);
    });

    const responses: Record<string, number> = {};
    page.on("response", (res) => {
      const url = res.url();
      if (url.includes("/hr/")) responses[url] = res.status();
    });

    await page.goto("/admin/employees?tab=disciplinary", { waitUntil: "networkidle", timeout: 180_000 });

    await expect(
      page.getByRole("heading", { name: "Disciplinary & Offboarding", exact: true }).first(),
    ).toBeVisible({ timeout: 60_000 });

    await expect
      .poll(() => hrRequests.some((u) => u.includes("/hr/disciplinary")), { timeout: 30_000 })
      .toBeTruthy();
    await expect
      .poll(() => hrRequests.some((u) => u.includes("/hr/offboarding")), { timeout: 30_000 })
      .toBeTruthy();

    await expect
      .poll(() => responses[Object.keys(responses).find((k) => k.includes("/hr/disciplinary")) ?? ""] ?? 0, {
        timeout: 30_000,
      })
      .toBe(200);

    expect(badRequests).toHaveLength(0);
  });

  test("HSE and Alumni tabs render gracefully without crashing", async ({ page }) => {
    test.slow();
    await page.goto("/admin/employees?tab=hse", { waitUntil: "networkidle", timeout: 180_000 });
    await expect(
      page.getByRole("heading", { name: /Health, Safety & Environment/i }).first(),
    ).toBeVisible({ timeout: 60_000 });

    await page.goto("/admin/employees?tab=alumni", { waitUntil: "networkidle", timeout: 180_000 });
    await expect(
      page.getByRole("heading", { name: /Alumni Network & Contractor Milestones/i }).first(),
    ).toBeVisible({ timeout: 60_000 });
  });
});
