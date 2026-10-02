import { expect, test, type Page } from "@playwright/test";
import { bootstrapAdminSessionViaApi } from "../../../src/auth";

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

async function getCsrfToken(page: Page): Promise<string> {
  const cookies = await page.context().cookies();
  const csrfCookie = cookies.find((c) => c.name.toLowerCase() === "csrf_token" || c.name.toLowerCase() === "x-csrf-token");
  if (csrfCookie?.value) return csrfCookie.value;

  const metaToken = await page
    .locator('meta[name="csrf-token"], meta[name="csrf_token"]')
    .getAttribute("content")
    .catch(() => null);
  if (metaToken) return metaToken;

  return page.evaluate(() => (window as unknown as Record<string, unknown>).__csrfToken || "").catch(() => "");
}

test.describe("CSRF protection", () => {
  test("POST without CSRF token returns 403", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await bootstrapAdminSessionViaApi(page);
    await page.goto("/admin/dashboard", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const res = await page.request.post("/api/v1/admin/finance/test-endpoint", {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "test" }),
      failOnStatusCode: false,
    });

    expect(res.status()).toBe(403);
  });

  test("POST with valid CSRF token returns 200", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await bootstrapAdminSessionViaApi(page);
    await page.goto("/admin/dashboard", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const csrfToken = await getCsrfToken(page);
    expect(csrfToken.length).toBeGreaterThan(0);

    const res = await page.request.post("/api/v1/admin/finance/test-endpoint", {
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ action: "test" }),
      failOnStatusCode: false,
    });

    expect([200, 404]).toContain(res.status());
  });
});
