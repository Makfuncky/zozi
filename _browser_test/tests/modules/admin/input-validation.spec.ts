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

test.describe("input validation", () => {
  test("oversized password rejected", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await bootstrapAdminSessionViaApi(page);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const oversizedPassword = "A".repeat(100);
    const res = await page.request.post("/api/auth/register", {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: `validation_${Date.now()}@zozi-test.com`,
        username: `validation_${Date.now()}`,
        password: oversizedPassword,
        role: "customer",
      }),
      failOnStatusCode: false,
    });

    expect([400, 422]).toContain(res.status());
  });

  test("SQL injection returns 422 or empty", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await bootstrapAdminSessionViaApi(page);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const res = await page.request.get("/api/v1/customer/catalog/products?q=DROP+TABLE+products", {
      failOnStatusCode: false,
    });

    expect([200, 204, 400, 422]).toContain(res.status());
    if (res.ok()) {
      const json = (await res.json()) as Record<string, unknown>;
      const items = Array.isArray(json.items) ? json.items : [];
      expect(items.length).toBe(0);
    }
  });

  test("XSS in address field sanitized", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await bootstrapAdminSessionViaApi(page);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const xssStreet = '<script>alert("xss")</script>123 Main St';
    const res = await page.request.post("/api/v1/customer/addresses", {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        street: xssStreet,
        city: "Dubai",
        country_code: "AE",
        is_default: true,
      }),
      failOnStatusCode: false,
    });

    if (res.ok()) {
      const json = (await res.json()) as Record<string, unknown>;
      const savedStreet = String(json.street || json.address?.street || "");
      expect(savedStreet).not.toContain("<script>");
      expect(savedStreet).not.toContain("</script>");
    } else {
      expect([400, 422]).toContain(res.status());
    }
  });
});
