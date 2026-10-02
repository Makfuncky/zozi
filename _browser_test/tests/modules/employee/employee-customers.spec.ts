import { expect, test, type Page } from "@playwright/test";
import {
  bootstrapEmployeeSession,
  openProtectedRoute,
  submitCredentialForm,
  waitForSessionFlag,
} from "../../../src/auth";
import { API_BASE } from "../../../src/api";

test.describe.configure({ timeout: 240_000 });

const SEED_EMPLOYEE_PASSWORD = process.env.SEED_EMPLOYEE_PASSWORD || "E2eEmployee#2026";

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

test.describe("employee customers", () => {
  test("employee can search customers", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);

    const hasApiSession = await bootstrapEmployeeSession(page);
    if (!hasApiSession) {
      await page.goto("/employee/login", { waitUntil: "domcontentloaded", timeout: 120_000 });
      await submitCredentialForm(page, "employee@zozi.com", SEED_EMPLOYEE_PASSWORD);
      await waitForSessionFlag(page);
    }

    await openProtectedRoute(page, "/employee/customers", /\/employee\/customers(?:\?|$)/, 120_000);

    await page.getByPlaceholder(/search customers/i).fill("test");
    await page.getByRole("button", { name: /search/i }).click();

    await expect(page.getByText(/results/i).first()).toBeVisible({ timeout: 60_000 });
  });

  test("employee can view customer order history", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);

    const hasApiSession = await bootstrapEmployeeSession(page);
    if (!hasApiSession) {
      await page.goto("/employee/login", { waitUntil: "domcontentloaded", timeout: 120_000 });
      await submitCredentialForm(page, "employee@zozi.com", SEED_EMPLOYEE_PASSWORD);
      await waitForSessionFlag(page);
    }

    await openProtectedRoute(page, "/employee/customers", /\/employee\/customers(?:\?|$)/, 120_000);

    await page.getByPlaceholder(/search customers/i).fill("test");
    await page.getByRole("button", { name: /search/i }).click();
    await page.waitForTimeout(2000);

    const firstResult = page.getByRole("link", { name: /customer/i }).first();
    if (await firstResult.isVisible().catch(() => false)) {
      await firstResult.click();
      await expectNavigation(page, /\/employee\/customers\/\d+(?:\/|$)/, 60_000);
      await expect(page.getByText(/order history/i).first()).toBeVisible({ timeout: 60_000 });
    } else {
      await expect(page.getByText(/no customers found/i)).toBeVisible({ timeout: 30_000 });
    }
  });
});
