import { expect, test, type Page } from "@playwright/test";

test.describe.configure({ timeout: 240_000 });

const BAD_CREDENTIALS = { email: "nonexistent@zozi-test.com", password: "WrongPass999!" };
const VALID_CREDENTIALS = { email: "customer@zozi.com", password: "E2eCustomer#2026" };

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

async function postLogin(page: Page, body: Record<string, unknown>) {
  return page.request.post("/api/auth/login", {
    headers: { "Content-Type": "application/json" },
    data: JSON.stringify(body),
    failOnStatusCode: false,
  });
}

test.describe("rate limiting", () => {
  test("15 rapid failed logins return 429", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    for (let i = 0; i < 14; i++) {
      const res = await postLogin(page, BAD_CREDENTIALS);
      expect([401, 429]).toContain(res.status());
    }

    const res15 = await postLogin(page, BAD_CREDENTIALS);
    expect(res15.status()).toBe(429);
  });

  test("rate limit resets after window", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    for (let i = 0; i < 14; i++) {
      await postLogin(page, BAD_CREDENTIALS);
    }
    await postLogin(page, BAD_CREDENTIALS);

    await page.waitForTimeout(65_000);

    const res = await postLogin(page, VALID_CREDENTIALS);
    expect([200, 401]).toContain(res.status());
  });
});
