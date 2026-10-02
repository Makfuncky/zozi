import { expect, test, type Page } from "@playwright/test";
import {
  bootstrapEmployeeSession,
  openProtectedRoute,
  submitCredentialForm,
  waitForSessionFlag,
} from "../../../src/auth";

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

test.describe("employee dashboard", () => {
  test("employee dashboard shows assigned orders and support tickets", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);

    const hasApiSession = await bootstrapEmployeeSession(page);
    if (!hasApiSession) {
      await page.goto("/employee/login", { waitUntil: "domcontentloaded", timeout: 120_000 });
      await submitCredentialForm(page, "employee@zozi.com", SEED_EMPLOYEE_PASSWORD);
      await waitForSessionFlag(page);
    }

    await openProtectedRoute(page, "/employee/dashboard", /\/employee(?:\/|$)/, 120_000);

    await expect(page.getByText(/assigned orders/i).first()).toBeVisible({ timeout: 60_000 });
    await expect(page.getByText(/support tickets/i).first()).toBeVisible({ timeout: 60_000 });
  });
});
