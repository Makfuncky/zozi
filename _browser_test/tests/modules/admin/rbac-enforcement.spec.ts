import { expect, test, type Page } from "@playwright/test";
import {
  bootstrapAdminSessionViaApi,
  bootstrapCustomerSession,
  bootstrapLogisticsSession,
  bootstrapSupplierSession,
} from "../../../src/auth";
import { apiGet, apiPost } from "../../../src/api";

test.describe.configure({ timeout: 240_000 });

async function mockExternalProviders(page: Page) {
  await page.route("**/api/v1/payments/stripe/**", (route) =>
    route.fulfill({ status: 200, body: JSON.stringify({ id: "mock_pi" }) }),
  );
  await page.route("**/api/v1/payments/paypal/**", (route) =>
    route.fulfill({ status: 200, body: JSON.stringify({ id: "mock_paypal" }) }),
  );
  await page.route("**/api/v1/comms/sms/**", (route) =>
    route.fulfill({ status: 200, body: JSON.stringify({ success: true }) }),
  );
  await page.route("**/api/v1/comms/email/**", (route) =>
    route.fulfill({ status: 200, body: JSON.stringify({ success: true }) }),
  );
}

test.describe("RBAC enforcement", () => {
  test("customer cannot access admin routes", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await bootstrapCustomerSession(page);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const res = await apiGet(page, "/api/v1/admin/finance");
    expect(res.status).toBe(403);
  });

  test("supplier cannot access other supplier's data", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await bootstrapSupplierSession(page);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const res = await apiGet(page, "/api/v1/admin/suppliers/999999");
    expect([403, 404]).toContain(res.status);
  });

  test("logistics cannot access admin finance", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await bootstrapLogisticsSession(page);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const res = await apiGet(page, "/api/v1/admin/finance");
    expect(res.status).toBe(403);
  });

  test("feature gate blocks unassigned feature", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await bootstrapCustomerSession(page);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const res = await apiPost(page, "/api/v1/admin/finance/ledger/post", { amount: 100, currency: "USD" });
    expect([403, 404]).toContain(res.status);
  });
});
