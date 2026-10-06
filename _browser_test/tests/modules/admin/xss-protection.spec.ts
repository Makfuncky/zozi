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

async function createProductWithXssName(page: Page): Promise<number> {
  const res = await page.request.post("/api/v1/admin/catalog/products", {
    headers: { "Content-Type": "application/json" },
    data: JSON.stringify({
      name: '<script>alert("xss")</script>Product',
      price: 100,
      currency: "USD",
      is_active: true,
    }),
    failOnStatusCode: false,
  });
  expect(res.ok()).toBe(true);
  const json = (await res.json()) as Record<string, unknown>;
  expect(typeof json.id).toBe("number");
  return json.id as number;
}

test.describe("XSS protection", () => {
  test("user-generated content is sanitized", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await bootstrapAdminSessionViaApi(page);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const productId = await createProductWithXssName(page);
    await page.goto(`/products/${productId}`, { waitUntil: "domcontentloaded", timeout: 120_000 });

    const hasScriptTag = await page
      .locator('script')
      .evaluateAll((nodes) => nodes.some((n) => n.textContent?.includes('alert("xss")')))
      .catch(() => false);

    expect(hasScriptTag).toBe(false);
    await expect(page.getByText(/<script>/i)).not.toBeVisible({ timeout: 30_000 });
  });

  test("CSP header present", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await bootstrapAdminSessionViaApi(page);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const response = await page.goto("/products", { waitUntil: "domcontentloaded", timeout: 120_000 });
    expect(response, "navigation to /products must return a response").not.toBeNull();
    const headers = response?.headers() ?? {};
    const cspHeader = headers["content-security-policy"] ?? "";
    expect(cspHeader, "CSP header must be present on production responses").not.toBe("");
    expect(cspHeader).toContain("script-src");
  });
});
