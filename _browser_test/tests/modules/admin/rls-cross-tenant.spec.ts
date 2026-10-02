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

test.describe("RLS cross-tenant isolation", () => {
  test("admin with country_code=AE cannot read SA data", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await bootstrapAdminSessionViaApi(page);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    await page.context().addCookies([
      {
        name: "zozi_country_override",
        value: "AE",
        domain: "127.0.0.1",
        path: "/",
        httpOnly: false,
        secure: false,
      },
    ]);

    const res = await page.request.get("/api/v1/admin/country/SA/summary", {
      failOnStatusCode: false,
    });

    expect([403, 404]).toContain(res.status());
  });

  test("customer sees only local-priced products", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await mockExternalProviders(page);
    await bootstrapAdminSessionViaApi(page);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    await page.context().addCookies([
      {
        name: "zozi_country_override",
        value: "AE",
        domain: "127.0.0.1",
        path: "/",
        httpOnly: false,
        secure: false,
      },
    ]);

    const res = await page.request.get("/api/v1/customer/catalog/products?limit=10", {
      failOnStatusCode: false,
    });
    expect(res.ok()).toBe(true);
    const json = (await res.json()) as Record<string, unknown>;
    const items = Array.isArray(json.items) ? json.items : [];
    const prices = (items as Array<Record<string, unknown>>).map((p) => p.currency).filter(Boolean);
    const uniqueCurrencies = Array.from(new Set(prices));
    if (uniqueCurrencies.length > 0) {
      expect(uniqueCurrencies.every((c) => c === "AED" || c === "USD")).toBe(true);
    }
  });
});
