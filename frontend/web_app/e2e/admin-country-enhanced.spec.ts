import { expect, test, type Page } from "@playwright/test";

test.describe.configure({ timeout: 240_000 });

async function waitForAdminNavigation(page: Page, expectedUrl: RegExp, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (expectedUrl.test(page.url())) return;
    await page.waitForTimeout(250);
  }
  throw new Error(`Timed out waiting for ${expectedUrl}. Current URL: ${page.url()}`);
}

async function waitForSessionFlag(page: Page, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const hasLocalSession = await page.evaluate(() => window.localStorage.getItem("zozi_has_session") === "1").catch(() => false);
    const cookies = await page.context().cookies();
    if (hasLocalSession || cookies.some((c) => c.name === "zozi_refresh" || c.name === "refresh_token")) return;
    await page.waitForTimeout(250);
  }
  throw new Error(`Timed out waiting for session state after ${timeoutMs}ms`);
}

async function hasSessionState(page: Page) {
  const hasLocalSession = await page.evaluate(() => window.localStorage.getItem("zozi_has_session") === "1").catch(() => false);
  const cookies = await page.context().cookies();
  return hasLocalSession || cookies.some((c) => c.name === "zozi_refresh" || c.name === "refresh_token");
}

async function isAdminAccessGateVisible(page: Page, timeoutMs = 3_000) {
  try {
    await page.getByRole("heading", { name: /Admin Access/i }).first().waitFor({ state: "visible", timeout: timeoutMs });
    return true;
  } catch {
    return false;
  }
}

async function openProtectedRoute(page: Page, path: string, expectedUrl: RegExp, timeoutMs = 60_000) {
  await page.goto(path, { waitUntil: "domcontentloaded", timeout: timeoutMs });
  await waitForAdminNavigation(page, expectedUrl, timeoutMs);
}

async function loginAsAdmin(page: Page, destination = "/admin/countries") {
  for (const candidate of ["admin@zozi.com", "admin"]) {
    const loginResponse = await page.request.post("/api/auth/login", {
      form: { username: candidate, password: "admin123" },
      failOnStatusCode: false,
    });
    if (!loginResponse.ok()) continue;
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    await openProtectedRoute(page, destination, /\/admin\/(dashboard|countries)(?:\?|$)/, 120_000);
    if (!(await isAdminAccessGateVisible(page))) return;
  }
  await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
  const submitButton = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await submitButton.waitFor();
  const form = submitButton.locator("xpath=ancestor::form[1]");
  const fillAndSubmit = async (username: string, password: string) => {
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
        identifierFilled = true;
        break;
      }
    }
    if (!identifierFilled) throw new Error("Unable to find a visible username/email input on the login form.");
    const passwordInput = form.locator("input[type='password']:visible").first();
    await passwordInput.fill(password);
    await submitButton.click();
  };
  await fillAndSubmit("admin@zozi.com", "admin123");
  try { await waitForSessionFlag(page, 30_000); } catch {
    await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
    await fillAndSubmit("admin", "admin123");
  }
  await waitForSessionFlag(page, 60_000);
  await openProtectedRoute(page, destination, /\/admin\/(dashboard|countries)(?:\?|$)/, 120_000);
  if (await isAdminAccessGateVisible(page)) {
    for (const candidate of ["admin@zozi.com", "admin"]) {
      const loginResponse = await page.request.post("/api/auth/login", {
        form: { username: candidate, password: "admin123" }, failOnStatusCode: false,
      });
      if (!loginResponse.ok()) continue;
      await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
      await page.request.get("/api/auth/me", { failOnStatusCode: false });
      await openProtectedRoute(page, destination, /\/admin\/(dashboard|countries)(?:\?|$)/, 120_000);
      if (!(await isAdminAccessGateVisible(page))) break;
    }
  }
  if (!(await hasSessionState(page))) throw new Error("Failed to establish admin session");
  await openProtectedRoute(page, destination, /\/admin\/countries(?:\?|$)/, 120_000);
}

async function selectCountryFromLedger(page: Page, code: string) {
  const row = page.getByTestId(`country-ledger-row-${code}`);
  await expect(row).toBeVisible({ timeout: 30_000 });
  await row.click();
  await expect(page.getByTestId("country-config-workspace")).toBeVisible({ timeout: 30_000 });
}

/* ────────────────────────────────────────────────────────────────────────────
   Tests
   ──────────────────────────────────────────────────────────────────────────── */

test.describe("Enhanced Country Features", () => {

  test("1. open and close new country inline form", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");
    await expect(page.getByRole("heading", { name: /Countries Ledger/i })).toBeVisible({ timeout: 120_000 });

    await page.getByTestId("add-country-button").click();
    await expect(page.getByTestId("new-country-modal")).toBeVisible({ timeout: 10_000 });

    // Close via Cancel
    await page.getByRole("button", { name: "Cancel" }).click();
    await expect(page.getByTestId("new-country-modal")).not.toBeVisible({ timeout: 5_000 });
  });

  test("2. auto-populate search panel appears in inline form", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");
    await page.getByTestId("add-country-button").click();
    await expect(page.getByTestId("new-country-modal")).toBeVisible({ timeout: 10_000 });

    // Auto-populate section visible
    await expect(page.getByText("Auto-populate from web")).toBeVisible();
    await expect(page.getByTestId("auto-populate-search-input")).toBeVisible();
    await expect(page.getByPlaceholder("Type a country name or code")).toBeVisible();
  });

  test("3. ledger table renders with existing countries", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");
    await expect(page.getByRole("heading", { name: /Countries Ledger/i })).toBeVisible({ timeout: 120_000 });

    // At least one row rendered
    const firstRow = page.locator("[data-testid^='country-ledger-row-']").first();
    await expect(firstRow).toBeVisible({ timeout: 30_000 });

    // Header columns present (use exact text to avoid strict mode violations)
    await expect(page.getByText("Country", { exact: true })).toBeVisible();
    await expect(page.getByText("Currency", { exact: true })).toBeVisible();
    await expect(page.getByText("Tax", { exact: true })).toBeVisible();
    await expect(page.getByText("Cities", { exact: true })).toBeVisible();
    await expect(page.getByText("Status", { exact: true })).toBeVisible();
  });

  test("4. expand country row shows detail workspace", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.locator("[data-testid^='country-ledger-row-']").first();
    await expect(firstRow).toBeVisible({ timeout: 30_000 });
    await firstRow.click();

    // Config workspace appears in expanded row
    await expect(page.getByTestId("country-config-workspace")).toBeVisible({ timeout: 30_000 });
    // Tab buttons visible
    await expect(page.getByRole("button", { name: "Overview" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Tax & VAT" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Internal Logistics" })).toBeVisible();
  });

  test("5. commission coverage summary visible", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");
    await selectCountryFromLedger(page, "OM");
    await page.getByRole("button", { name: "Category Commissions" }).click();
    await expect(page.getByTestId("country-commission-panel")).toBeVisible({ timeout: 15_000 });
  });

  test("6. payout rules tab has category and product sections", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");
    await selectCountryFromLedger(page, "OM");

    // Navigate to Payout Settings tab
    await page.getByRole("button", { name: "Payout Settings" }).click();
    await expect(page.getByText("Supplier Settlement & Payout Rules")).toBeVisible({ timeout: 15_000 });

    // Category payout override section (heading)
    await expect(page.getByText("Category-Level Payout Overrides", { exact: true })).toBeVisible({ timeout: 10_000 });
    // Product payout override section (heading)
    await expect(page.getByText("Product-Level Payout Overrides", { exact: true })).toBeVisible({ timeout: 10_000 });
  });

  test("7. payout rules — add category rule", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");
    await selectCountryFromLedger(page, "OM");

    await page.getByRole("button", { name: "Payout Settings" }).click();
    await expect(page.getByText("Supplier Settlement & Payout Rules")).toBeVisible({ timeout: 15_000 });

    // Click Add button
    const addBtn = page.getByRole("button", { name: /Add.*Category.*Rule/i });
    if (await addBtn.isVisible().catch(() => false)) {
      await addBtn.click();
      // Should see success/error feedback
      await expect(page.getByTestId("country-activity-message")).toBeVisible({ timeout: 10_000 });
    }
  });

  test("8. payout rules — add product rule", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");
    await selectCountryFromLedger(page, "OM");

    await page.getByRole("button", { name: "Payout Settings" }).click();
    await expect(page.getByText("Supplier Settlement & Payout Rules")).toBeVisible({ timeout: 15_000 });

    const addBtn = page.getByRole("button", { name: /Add.*Product.*Rule/i });
    if (await addBtn.isVisible().catch(() => false)) {
      await addBtn.click();
      await expect(page.getByTestId("country-activity-message")).toBeVisible({ timeout: 10_000 });
    }
  });

  test("9. expand ledger row and navigate all tabs", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.locator("[data-testid^='country-ledger-row-']").first();
    await firstRow.click();
    await expect(page.getByTestId("country-config-workspace")).toBeVisible({ timeout: 30_000 });

    // Verify all 12 tab buttons exist
    const tabs = [
      "Overview", "Tax & VAT", "Internal Logistics", "Delivery Partners",
      "Payment Gateways", "Legal & Rules", "Regions & Cities",
      "Supplier KYC", "Payout Settings", "Value Commissions",
      "Category Commissions", "Version History",
    ];
    for (const tab of tabs) {
      await expect(page.getByRole("button", { name: tab })).toBeVisible({ timeout: 10_000 });
    }
  });

  test("10. bulk set commission overlay opens", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");
    await selectCountryFromLedger(page, "OM");

    await page.getByRole("button", { name: "Category Commissions" }).click();
    await expect(page.getByTestId("country-commission-panel")).toBeVisible({ timeout: 15_000 });

    // Bulk set button
    const bulkBtn = page.getByRole("button", { name: /Bulk Set/i });
    if (await bulkBtn.isVisible().catch(() => false)) {
      await bulkBtn.click();
      // Should see a rate input or dialog
      await expect(page.locator("input[type='number']").first()).toBeVisible({ timeout: 5_000 });
    }
  });

  test("11. admin country selector visible for correct role", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    // Full admin should NOT see the country selector (it's for country_head/country_manager)
    const selector = page.getByTestId("country-select-dropdown");
    const visible = await selector.isVisible().catch(() => false);
    // Admin sees all countries so the selector should not appear
    expect(visible).toBe(false);
  });

  test("12. version history tab loads", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    await selectCountryFromLedger(page, "OM");
    await page.getByRole("button", { name: "Version History" }).click();
    await expect(page.getByTestId("country-versions-panel")).toBeVisible({ timeout: 15_000 });
  });

  test("13. reload country workspace button works", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");
    await selectCountryFromLedger(page, "OM");

    const reloadBtn = page.getByTestId("reload-country-workspace");
    if (await reloadBtn.isVisible().catch(() => false)) {
      await reloadBtn.click();
      await expect(page.getByTestId("country-config-workspace")).toBeVisible({ timeout: 15_000 });
    }
  });

  test("14. auto-populate 'Saudi Arabia' returns correct data", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");
    await page.getByTestId("add-country-button").click();
    await expect(page.getByTestId("new-country-modal")).toBeVisible({ timeout: 10_000 });

    const searchInput = page.getByTestId("auto-populate-search-input");
    await expect(searchInput).toBeVisible();

    // Type "Saudi Arabia" and click the Search button (bypasses 600ms debounce)
    await searchInput.fill("Saudi Arabia");
    await page.getByRole("button", { name: "Search" }).click();

    // Wait for response
    await page.waitForTimeout(3_000);

    // Check for toast errors first (missing API key, demo key, etc.)
    const errorText = await page.locator("p.text-xs.font-medium").first().textContent().catch(() => "");
    if (errorText && (errorText.includes("API key") || errorText.includes("REST_COUNTRIES") || errorText.includes("not configured") || errorText.includes("demo key") || errorText.includes("Could not find country data"))) {
      test.fail(true, `Auto-populate failed with backend error: "${errorText}". Ensure REST_COUNTRIES_API_KEY is set in backend/.env`);
    }

    // Wait for fields to be populated
    const codeInput = page.locator("input[placeholder='AE']");
    await expect(codeInput).toBeVisible({ timeout: 5_000 });
    const codeValue = await codeInput.inputValue();
    expect(codeValue.toUpperCase()).toBe("SA");

    const nameInput = page.locator("input[placeholder='United Arab Emirates']");
    await expect(nameInput).toBeVisible();
    const nameValue = await nameInput.inputValue();
    expect(nameValue.toLowerCase()).toContain("saudi");

    const currencyInput = page.locator("input[placeholder='AED']");
    await expect(currencyInput).toBeVisible();
    const currencyValue = await currencyInput.inputValue();
    expect(currencyValue.length).toBeGreaterThan(0);

    const tzInput = page.locator("input[placeholder='Asia/Dubai']");
    await expect(tzInput).toBeVisible();
    const tzValue = await tzInput.inputValue();
    expect(tzValue.length).toBeGreaterThan(0);

    // Close the form
    await page.getByRole("button", { name: "Cancel" }).click();
    await expect(page.getByTestId("new-country-modal")).not.toBeVisible({ timeout: 5_000 });
  });

});
