import { expect, test } from "@playwright/test";
import {
  expectNavigation,
  waitForSessionFlag,
  openProtectedRoute,
  bootstrapSessionViaApi,
  submitCredentialForm,
} from "./helpers/auth";

test.describe.configure({ timeout: 120_000 });

test.describe("auth role login smoke", () => {
  test("customer login reaches authenticated customer pages", async ({ page }) => {
    test.slow();

    const hasApiSession = await bootstrapSessionViaApi(page, ["customer@zozi.com", "customer"], "customer123");
    if (!hasApiSession) {
      await page.goto("/login");
      await submitCredentialForm(page, "customer@zozi.com", "customer123");
      await waitForSessionFlag(page);
    }

    await openProtectedRoute(page, "/products", /\/products(?:\?|$)/, 60_000);
    await openProtectedRoute(page, "/orders", /\/orders(?:\?|$)/, 30_000);
  });

  test("admin login reaches admin dashboard", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    const hasApiSession = await bootstrapSessionViaApi(page, ["admin@zozi.com", "admin"], "admin123");
    if (!hasApiSession) {
      await page.goto("/admin/login");
      await submitCredentialForm(page, "admin@zozi.com", "admin123");
      await waitForSessionFlag(page);
    }

    await openProtectedRoute(page, "/admin/dashboard", /\/admin\/dashboard(?:\?|$)/, 120_000);
  });

  test("supplier login reaches supplier dashboard", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    const hasApiSession = await bootstrapSessionViaApi(page, ["supplier@zozi.com", "supplier"], "supplier123");
    if (!hasApiSession) {
      await page.goto("/supplier/login");
      await submitCredentialForm(page, "supplier@zozi.com", "supplier123");
      await waitForSessionFlag(page);
    }

    await openProtectedRoute(page, "/supplier/dashboard", /\/supplier\/dashboard(?:\?|$)/, 60_000);
  });

  test("logistics partner login reaches logistics dashboard", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    const hasApiSession = await bootstrapSessionViaApi(page, ["logistics@zozi.com", "logistics"], "logistics123");
    if (!hasApiSession) {
      await page.goto("/logistics-partner/login");
      await submitCredentialForm(page, "logistics@zozi.com", "logistics123");
      await waitForSessionFlag(page);
    }

    await openProtectedRoute(page, "/logistics-partner/dashboard", /\/logistics-partner\/dashboard(?:\?|$)/, 120_000);
  });
});
