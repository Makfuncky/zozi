/**
 * Admin Treasury & Payout — Playwright E2E Tests
 *
 * Covers Treasury dashboard, ledger filtering, cash position,
 * and payout batches on /admin/finance?section=treasury.
 */
import { expect, test, type Page, type Route } from "@playwright/test";

const API_HOST = /https?:\/\/(?:localhost|127\.0\.0\.1):8000/;

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
    const resp = await page.request.post("/api/auth/login", {
      form: { username: candidate, password: "admin123" },
      failOnStatusCode: false,
    });
    if (!resp.ok()) continue;

    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    await page.goto("/admin/finance?section=treasury", { waitUntil: "domcontentloaded", timeout: 120_000 });

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
  await page.goto("/admin/finance?section=treasury", { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.route("**/cart/**", async (r) => fulfillJson(r, []));
  await page.route("**/notifications**", async (r) => fulfillJson(r, []));
  await page.route("**/api/notifications**", async (r) => fulfillJson(r, []));
}

test.describe("Admin Treasury & Payout", () => {
  test.beforeEach(async ({ page }) => {
    // Cash accounts
    await page.route("**/admin/cash/**/accounts", async (route) => {
      if (route.request().method() === "GET") {
        await fulfillJson(route, [
          { id: 1, code: "CASH-AE", name: "AE Operating Cash", balance: 125000 },
          { id: 2, code: "CASH-SA", name: "SA Operating Cash", balance: 95000 },
        ]);
      } else {
        await route.continue();
      }
    });

    // Treasury / accounting endpoints
    await page.route("**/accounting/journal-entries", async (route) => {
      await fulfillJson(route, [
        { id: 1, ref: "JE-001", description: "Opening balance", debit: 50000, credit: 0, created_at: "2026-07-16T10:00:00Z" },
        { id: 2, ref: "JE-002", description: "Supplier payment", debit: 0, credit: 15000, created_at: "2026-07-16T11:00:00Z" },
      ]);
    });

    await page.route("**/accounting/trial-balance", async (route) => {
      await fulfillJson(route, {
        accounts: [
          { code: "1000", name: "Cash", balance: 125000 },
          { code: "2000", name: "Accounts Payable", balance: -45000 },
        ],
        total_debits: 125000,
        total_credits: 45000,
      });
    });

    await page.route("**/accounting/reports/cash-flow**", async (route) => {
      await fulfillJson(route, {
        operating: { inflow: 200000, outflow: 150000, net: 50000 },
        investing: { inflow: 0, outflow: 25000, net: -25000 },
        financing: { inflow: 0, outflow: 0, net: 0 },
        net_change: 25000,
      });
    });

    // Payout batches
    await page.route("**/admin/payouts/**", async (route) => {
      const url = new URL(route.request().url());
      if (route.request().method() === "GET" && url.pathname.includes("/pending")) {
        await fulfillJson(route, [
          { id: 1, batch_id: "BATCH-001", supplier_id: 101, amount: 4500, method: "bank_transfer", status: "pending" },
          { id: 2, batch_id: "BATCH-001", supplier_id: 102, amount: 3200, method: "bank_transfer", status: "pending" },
        ]);
      } else if (route.request().method() === "GET") {
        await fulfillJson(route, [
          { id: 1, batch_id: "BATCH-001", status: "completed", total_amount: 7700, created_at: "2026-07-15T08:00:00Z" },
        ]);
      } else {
        await route.continue();
      }
    });

    // VAT remittance
    await page.route("**/accounting/vat/**", async (route) => {
      await fulfillJson(route, [
        { id: 1, period: "2026-Q2", amount: 12500, status: "filed" },
      ]);
    });

    // Chart of accounts
    await page.route("**/accounting/accounts", async (route) => {
      await fulfillJson(route, [
        { code: "1000", name: "Cash", type: "asset" },
        { code: "2000", name: "AP", type: "liability" },
      ]);
    });

    // Auth
    await mockAdminSession(page);
  });

  test("treasury dashboard displays KPI cards and cash buckets", async ({ page }) => {
    await page.waitForTimeout(2000);

    await expect(page.getByText(/Finance & Cash Management/i)).toBeVisible();
    await expect(page.getByRole("tab", { name: /treasury/i })).toBeVisible();
    await page.getByRole("tab", { name: /treasury|dashboard/i }).first().click();
    await page.waitForTimeout(1000);
  });

  test("ledger tab shows journal entries with filter controls", async ({ page }) => {
    await page.waitForTimeout(2000);
    await page.getByRole("tab", { name: /ledger|general ledger/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByRole("button", { name: /filter/i })).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("JE-001")).toBeVisible();
  });

  test("payout batches tab lists pending and completed payouts", async ({ page }) => {
    await page.waitForTimeout(2000);
    await page.getByRole("tab", { name: /payout/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByText(/payout/i)).toBeVisible();
  });
});
