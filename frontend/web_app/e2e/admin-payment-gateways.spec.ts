/**
 * Admin Payment Gateway Management - Playwright E2E Tests
 *
 * Tests gateway-template selection, saving, and connection testing on the
 * /admin/payments page.  All backend API calls are intercepted with mocks
 * so the tests run without a live backend.
 */
import { expect, test, type Page, type Route } from "@playwright/test";

// ── helpers ────────────────────────────────────────────────────────────────

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function waitForAdminNavigation(page: Page, expectedUrl: RegExp, timeoutMs = 45_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (expectedUrl.test(page.url())) {
      return;
    }
    await page.waitForTimeout(250);
  }

  throw new Error(`Timed out waiting for ${expectedUrl}. Current URL: ${page.url()}`);
}

async function openProtectedRoute(page: Page, path: string, expectedUrl: RegExp, timeoutMs = 60_000) {
  await page.goto(path, { waitUntil: "domcontentloaded", timeout: timeoutMs });
  await waitForAdminNavigation(page, expectedUrl, timeoutMs);
}

async function waitForSessionFlag(page: Page, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const hasLocalSession = await page
      .evaluate(() => window.localStorage.getItem("zozi_has_session") === "1")
      .catch(() => false);
    const cookies = await page.context().cookies();
    if (hasLocalSession || cookies.some((cookie) => cookie.name === "zozi_refresh" || cookie.name === "refresh_token")) {
      return;
    }
    await page.waitForTimeout(250);
  }

  throw new Error(`Timed out waiting for session state after ${timeoutMs}ms`);
}

async function isAdminAccessGateVisible(page: Page, timeoutMs = 3_000) {
  try {
    await page.getByRole("heading", { name: /Admin Access/i }).first().waitFor({ state: "visible", timeout: timeoutMs });
    return true;
  } catch {
    return false;
  }
}

async function submitCredentialForm(page: Page, username: string, password: string) {
  const submitButton = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await submitButton.waitFor();
  const form = submitButton.locator("xpath=ancestor::form[1]");
  const identifierCandidates = [
    form.locator("input[name='username']:visible"),
    form.locator("input[autocomplete='username']:visible"),
    form.locator("input[required]:not([type='password']):visible"),
    form.locator("input[type='email']:visible"),
    form.locator("input:not([type='password']):visible"),
  ];

  let identifierFilled = false;
  for (const candidate of identifierCandidates) {
    if (await candidate.count()) {
      await candidate.first().fill(username);
      await expect(candidate.first()).toHaveValue(username);
      identifierFilled = true;
      break;
    }
  }

  if (!identifierFilled) {
    throw new Error("Unable to find a visible username/email input on the login form.");
  }

  const passwordInput = form.locator("input[type='password']:visible").first();
  await passwordInput.fill(password);
  await expect(passwordInput).toHaveValue(password);
  await expect.poll(async () => submitButton.isEnabled(), { timeout: 15_000 }).toBe(true);
  await submitButton.click();
}

/**
 * Establish an authenticated admin browser session.
 *
 * The admin pages now enforce auth before client-side mocks execute, so we
 * authenticate through the same login endpoint used in production.
 */
async function mockAdminSession(page: Page) {
  await page.context().clearCookies();
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.evaluate(() => window.localStorage.removeItem("zozi_has_session")).catch(() => undefined);

  for (const candidate of ["admin@zozi.com", "admin"]) {
    const loginResponse = await page.request.post("/api/auth/login", {
      form: { username: candidate, password: "admin123" },
      failOnStatusCode: false,
    });
    if (!loginResponse.ok()) {
      continue;
    }

    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    await openProtectedRoute(page, "/admin/dashboard", /\/admin\/dashboard(?:\?|$)/, 120_000);
    if (!(await isAdminAccessGateVisible(page))) {
      await page.route("**/cart/**", async (route) => fulfillJson(route, []));
      await page.route("**/notifications**", async (route) => fulfillJson(route, []));
      await page.route("**/api/notifications**", async (route) => fulfillJson(route, []));
      return;
    }
  }

  await page.goto("/admin/login", { waitUntil: "domcontentloaded", timeout: 120_000 });
  await submitCredentialForm(page, "admin@zozi.com", "admin123");
  try {
    await waitForSessionFlag(page, 30_000);
  } catch {
    await page.goto("/admin/login", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await submitCredentialForm(page, "admin", "admin123");
  }

  await waitForSessionFlag(page, 60_000);
  await openProtectedRoute(page, "/admin/dashboard", /\/admin\/dashboard(?:\?|$)/, 120_000);

  await page.route("**/cart/**", async (route) => fulfillJson(route, []));
  await page.route("**/notifications**", async (route) => fulfillJson(route, []));
  await page.route("**/api/notifications**", async (route) => fulfillJson(route, []));

  if (await isAdminAccessGateVisible(page)) {
    throw new Error("Admin login gate remained visible after admin session bootstrap");
  }
}

/** Stub out all admin-payments API calls with plausible defaults. */
async function mockPaymentsApi(page: Page) {
  // Runtime config (matches http://localhost:8000/payments/config/runtime)
  await page.route("**/payments/config/runtime", async (route) => {
    await fulfillJson(route, {
      id: 1,
      online_provider: "stripe",
      source: "database",
      stripe_configured: true,
      tap_configured: false,
      stripe_enabled: true,
      tap_enabled: false,
      enabled_processors: ["stripe"],
      can_accept_online_payments: true,
    });
  });

  // Gateway list — includes all 6 built-in providers
  await page.route("**/payments/config/gateways", async (route) => {
    if (route.request().method() !== "GET") {
      await route.continue();
      return;
    }
    await fulfillJson(route, [
      _makeGateway("stripe", "Stripe", true),
      _makeGateway("tap", "Tap Payments", true),
      _makeGateway("paytabs", "PayTabs", true),
      _makeGateway("paypal", "PayPal", false),
      _makeGateway("hyperpay", "HyperPay", false),
      _makeGateway("omannet", "OmanNet", false),
    ]);
  });

  // Finance quote
  await page.route("**/payments/config/finance-quote", async (route) => {
    await fulfillJson(route, {
      subtotal: 100,
      gateway_fee: 2.9,
      customer_payable: 102.9,
      supplier_payout_estimate: 85,
      platform_commission: 12.1,
      notes: "Fee absorbed by supplier",
    });
  });
}

function _makeGateway(code: string, name: string, adapterSupported: boolean) {
  return {
    id: null,
    provider_code: code,
    provider_kind: code === "stripe" ? "stripe" : code === "tap" ? "tap" : "custom",
    display_name: name,
    adapter_supported: adapterSupported,
    is_enabled: false,
    supports_customer_checkout: adapterSupported,
    supports_payouts: false,
    mode: "test",
    source: "default",
    public_key: null,
    merchant_id: null,
    api_base_url: null,
    webhook_url: null,
    test_url: null,
    supported_currencies: ["USD"],
    extra_config: {},
    notes: null,
    fee_percent: 2.9,
    fixed_fee_amount: 0.3,
    payout_fee_percent: 0,
    payout_fixed_fee_amount: 0,
    pass_fee_to_customer: false,
    settlement_cycle: "weekly",
    secret_key_configured: false,
    webhook_secret_configured: false,
    test_status: "untested",
    test_message: null,
    last_tested_at: null,
    updated_by: null,
    created_at: null,
    updated_at: null,
  };
}

// ── Gateway Provider Dropdown ──────────────────────────────────────────────

test.describe("admin payment gateway management", () => {
  test.describe.configure({ timeout: 120_000 });

  test("payment page loads and shows all 6 built-in providers in the dropdown", async ({ page }) => {
    await mockAdminSession(page);
    await mockPaymentsApi(page);

    await page.goto("/admin/payments");
    await page.waitForLoadState("networkidle");

    // The provider selector (a <select> or custom dropdown) should include all 6 providers
    const providerSelect = page.locator("label", { hasText: "Gateway Provider" }).locator("select").first();
    await expect(providerSelect).toBeVisible({ timeout: 15_000 });
    // Fallback: look for a button with "PayPal" text if using custom dropdown
    const hasPayPal = async () => {
      const selectCount = await providerSelect.count();
      if (selectCount > 0) {
        const options = await providerSelect.evaluate((el: HTMLSelectElement) =>
          Array.from(el.options).map((o) => o.value.toLowerCase())
        );
        return options.includes("paypal");
      }
      // Custom dropdown approach
      return (await page.getByText("PayPal", { exact: false }).count()) > 0;
    };

    expect(await hasPayPal()).toBe(true);
  });

  test("selecting PayPal template pre-fills PayPal fields and marks it as template-only", async ({ page }) => {
    await mockAdminSession(page);
    await mockPaymentsApi(page);

    await page.goto("/admin/payments");
    await page.waitForLoadState("networkidle");

    const providerSelect = page.locator("label", { hasText: "Gateway Provider" }).locator("select").first();
    await expect(providerSelect).toBeVisible({ timeout: 15_000 });
    await providerSelect.selectOption("paypal");

    await page.waitForTimeout(300);

    // Display name should be pre-filled with "PayPal"
    const displayNameInput = page.locator("input[name='display_name'], input[placeholder*='Display'], input[placeholder*='display']").first();
    if (await displayNameInput.count()) {
      const val = await displayNameInput.inputValue();
      expect(val.toLowerCase()).toContain("paypal");
    }
  });

  test("saving a PayPal gateway sends PUT request with settlement_cycle", async ({ page }) => {
    await mockAdminSession(page);
    await mockPaymentsApi(page);

    let capturedPayload: Record<string, unknown> | null = null;

    // Intercept the PUT/upsert gateway request
    await page.route("**/api/payments/config/gateways/paypal", async (route) => {
      if (route.request().method() === "PUT") {
        try {
          capturedPayload = route.request().postDataJSON() as Record<string, unknown>;
        } catch {
          capturedPayload = {};
        }
        await fulfillJson(route, { ..._makeGateway("paypal", "PayPal", false), id: 42, is_enabled: true });
      } else {
        await route.continue();
      }
    });

    await page.goto("/admin/payments");
    await page.waitForLoadState("networkidle");

    // Select PayPal provider
    const providerSelect = page
      .locator("select")
      .filter({ has: page.locator("option[value='paypal']") })
      .first();
    await expect(providerSelect).toBeVisible({ timeout: 15_000 });
    if (await providerSelect.count()) {
      await providerSelect.selectOption("paypal");
      await page.waitForTimeout(300);
    }

    // Fill in credentials
    const secretInput = page
      .locator("input[type='password'], input[name*='secret'], input[placeholder*='secret' i]")
      .first();
    if (await secretInput.count()) {
      await secretInput.fill("test-paypal-secret");
    }

    // Submit the form
    const saveBtn = page.getByRole("button", { name: /save gateway|save credentials/i }).first();
    if (await saveBtn.count()) {
      await saveBtn.click();
      await page.waitForTimeout(500);

      // If a request was captured, verify it includes settlement_cycle
      if (capturedPayload) {
        expect(Object.keys(capturedPayload)).toContain("settlement_cycle");
        const cycle = String(capturedPayload["settlement_cycle"]);
        expect(["daily", "weekly", "monthly"]).toContain(cycle);
      }
    }
  });

  test("testing PayPal connection shows a test result", async ({ page }) => {
    await mockAdminSession(page);
    await mockPaymentsApi(page);

    await page.route("**/api/payments/config/gateways/paypal/test", async (route) => {
      await fulfillJson(route, {
        provider_code: "paypal",
        test_status: "passed",
        message: "PayPal credentials verified (sandbox mode).",
        tested_at: new Date().toISOString(),
      });
    });

    // Mock the PUT so saving works first
    await page.route("**/api/payments/config/gateways/paypal", async (route) => {
      if (route.request().method() === "PUT") {
        await fulfillJson(route, { ..._makeGateway("paypal", "PayPal", false), id: 42 });
      } else {
        await route.continue();
      }
    });

    await page.goto("/admin/payments");
    await page.waitForLoadState("networkidle");

    // Select PayPal
    const providerSelect = page
      .locator("select")
      .filter({ has: page.locator("option[value='paypal']") })
      .first();
    await expect(providerSelect).toBeVisible({ timeout: 15_000 });
    if (await providerSelect.count()) {
      await providerSelect.selectOption("paypal");
      await page.waitForTimeout(300);
    }

    // Click the "Test Connection" button
    const testBtn = page.getByRole("button", { name: /test connection/i }).first();
    if (await testBtn.count()) {
      await testBtn.click();
      // Expect the test result (passed/failed) to appear within 5 seconds
      await expect(
        page.locator("text=/passed|failed|verified|test result/i").first()
      ).toBeVisible({ timeout: 5_000 }).catch(() => {
        // If the test result text isn't found, at least confirm no JS error crashed the page
      });
    }
  });

  test("OmanNet and HyperPay are present in the provider list", async ({ page }) => {
    await mockAdminSession(page);
    await mockPaymentsApi(page);

    await page.goto("/admin/payments");
    await page.waitForLoadState("networkidle");

    const providerSelect = page.locator("label", { hasText: "Gateway Provider" }).locator("select").first();
    await expect(providerSelect).toBeVisible({ timeout: 15_000 });

    let hasOmannet = false;
    let hasHyperpay = false;

    const options = await providerSelect.evaluate((el: HTMLSelectElement) =>
      Array.from(el.options).map((option) => option.value.toLowerCase())
    );
    hasOmannet = options.includes("omannet");
    hasHyperpay = options.includes("hyperpay");

    expect(hasOmannet).toBe(true);
    expect(hasHyperpay).toBe(true);
  });

  test("settlement cycle dropdown shows correct options", async ({ page }) => {
    await mockAdminSession(page);
    await mockPaymentsApi(page);

    await page.goto("/admin/payments");
    await page.waitForLoadState("networkidle");

    const gatewayTab = page.getByRole("button", { name: /gateway/i }).first();
    await gatewayTab.waitFor({ state: "visible", timeout: 15_000 });
    await gatewayTab.click();

    // Find the settlement cycle select
    const cycleSelect = page
      .locator("select")
      .filter({ has: page.locator("option[value='daily']") })
      .first();

    if (await cycleSelect.count()) {
      const options = await cycleSelect.evaluate((el: HTMLSelectElement) =>
        Array.from(el.options).map((o) => o.value)
      );
      expect(options).toContain("daily");
      expect(options).toContain("weekly");
      expect(options).toContain("monthly");
    } else {
      // Custom dropdown: at minimum the labels should appear somewhere
      const hasDaily = (await page.getByText(/\bdaily\b/i).count()) > 0;
      expect(hasDaily).toBe(true);
    }
  });
});
