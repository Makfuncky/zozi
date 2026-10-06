import { expect, test, type Page } from "@playwright/test";
import {
  bootstrapEmployeeSession,
  expectNavigation,
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

async function fetchAssignedOrderId(page: Page): Promise<number> {
  const res = await page.request.get(`${API_BASE}/api/v1/employee/orders?limit=50`, {
    failOnStatusCode: false,
  });
  expect(res.ok()).toBe(true);
  const json = (await res.json()) as Record<string, unknown>;
  const items = Array.isArray(json.items) ? json.items : (json as unknown as Array<{ id?: number }>);
  const order = items.find((o: { id?: number }) => typeof o.id === "number");
  if (!order?.id) throw new Error("No assigned order found for employee");
  return order.id;
}

test.describe("employee orders", () => {
  test("employee can view order detail", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);

    const hasApiSession = await bootstrapEmployeeSession(page);
    if (!hasApiSession) {
      await page.goto("/employee/login", { waitUntil: "domcontentloaded", timeout: 120_000 });
      await submitCredentialForm(page, "employee@zozi.com", SEED_EMPLOYEE_PASSWORD);
      await waitForSessionFlag(page);
    }

    const orderId = await fetchAssignedOrderId(page);
    await page.goto(`/employee/orders/${orderId}`, { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expectNavigation(page, new RegExp(`/employee/orders/${orderId}(?:\\?|$)`), 90_000);
    await expect(page.getByRole("heading", { name: /order details/i })).toBeVisible({ timeout: 60_000 });
  });

  test("employee can add internal note to order", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);

    const hasApiSession = await bootstrapEmployeeSession(page);
    if (!hasApiSession) {
      await page.goto("/employee/login", { waitUntil: "domcontentloaded", timeout: 120_000 });
      await submitCredentialForm(page, "employee@zozi.com", SEED_EMPLOYEE_PASSWORD);
      await waitForSessionFlag(page);
    }

    const orderId = await fetchAssignedOrderId(page);
    await page.goto(`/employee/orders/${orderId}`, { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expectNavigation(page, new RegExp(`/employee/orders/${orderId}(?:\\?|$)`), 90_000);

    const noteText = `E2E internal note ${Date.now()}`;
    await page.getByLabel(/internal note/i).fill(noteText);
    await page.getByRole("button", { name: /add note|submit note/i }).click();

    await expect(page.getByText(noteText)).toBeVisible({ timeout: 60_000 });
  });
});
