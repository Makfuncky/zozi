import { expect, test, type Page } from "@playwright/test";
import { bootstrapAdminSessionViaApi } from "./helpers/auth";

test.describe.configure({ timeout: 240_000 });

async function waitForAdminNavigation(page: Page, expectedUrl: RegExp, timeoutMs = 60_000) {
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

async function hasSessionState(page: Page) {
  const hasLocalSession = await page
    .evaluate(() => window.localStorage.getItem("zozi_has_session") === "1")
    .catch(() => false);
  const cookies = await page.context().cookies();
  return hasLocalSession || cookies.some((cookie) => cookie.name === "zozi_refresh" || cookie.name === "refresh_token");
}

async function isAdminAccessGateVisible(page: Page, timeoutMs = 3_000) {
  try {
    await page.getByRole("heading", { name: /Admin Access/i }).first().waitFor({ state: "visible", timeout: timeoutMs });
    return true;
  } catch {
    return false;
  }
}

async function loginAsAdmin(page: Page, destination = "/admin/countries") {
  for (const candidate of ["admin@zozi.com", "admin"]) {
    await bootstrapAdminSessionViaApi(page);

    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    await openProtectedRoute(page, destination, /\/admin\/(dashboard|countries)(?:\?|$)/, 120_000);
    if (!(await isAdminAccessGateVisible(page))) {
      return;
    }
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

    if (!identifierFilled) {
      throw new Error("Unable to find a visible username/email input on the login form.");
    }

    const passwordInput = form.locator("input[type='password']:visible").first();
    await passwordInput.fill(password);
    await submitButton.click();
  };

  await fillAndSubmit("admin@zozi.com", "admin123");
  try {
    await waitForSessionFlag(page, 30_000);
  } catch {
    await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
    await fillAndSubmit("admin", "admin123");
  }

  await waitForSessionFlag(page, 60_000);
  await openProtectedRoute(page, destination, /\/admin\/(dashboard|countries)(?:\?|$)/, 120_000);

  if (await isAdminAccessGateVisible(page)) {
    for (const candidate of ["admin@zozi.com", "admin"]) {
      await bootstrapAdminSessionViaApi(page);
      await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
      await page.request.get("/api/auth/me", { failOnStatusCode: false });
      await openProtectedRoute(page, destination, /\/admin\/(dashboard|countries)(?:\?|$)/, 120_000);
      if (!(await isAdminAccessGateVisible(page))) {
        break;
      }
    }
  }

  if (!(await hasSessionState(page))) {
    throw new Error("Failed to establish admin session for country control plane test");
  }

  await openProtectedRoute(page, destination, /\/admin\/countries(?:\?|$)/, 120_000);
}

/* ── Helper: select a country from the ledger table by code ───────────────── */
async function selectCountryFromLedger(page: Page, code: string) {
  const row = page.getByTestId(`country-ledger-row-${code}`);
  await expect(row).toBeVisible({ timeout: 30_000 });
  await row.click();
  // Wait for the workspace to load
  await expect(page.getByText(/Sections/)).toBeVisible({ timeout: 30_000 });
}

/* ── Helper: create a draft and expect success ────────────────────────────── */
async function saveDraft(page: Page, buttonLabel: string | RegExp, expectedActivity: RegExp) {
  const btn = page.getByRole("button", { name: buttonLabel });
  await expect(btn).toBeVisible({ timeout: 10_000 });
  await btn.click();
  await expect(page.getByTestId("country-activity-message")).toContainText(expectedActivity, { timeout: 30_000 });
  // Back to Overview after saving
  await page.getByRole("button", { name: "Overview" }).click();
}

/* ────────────────────────────────────────────────────────────────────────────
   Tests
   ──────────────────────────────────────────────────────────────────────────── */

test.describe("Country Ledger & Configuration Workspace", () => {

  test("1. ledger table renders with existing countries", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    await expect(page.getByRole("heading", { name: /Country Configuration Ledger/i })).toBeVisible({ timeout: 120_000 });

    const table = page.locator("table").first();
    await expect(table).toBeVisible({ timeout: 30_000 });

    const rows = table.locator("tbody tr");
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test("2. create a new country via the compact form", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const testCode = "XZ";
    const testName = "Testland";

    // Fill create form
    await page.getByTestId("create-country-code").fill(testCode);
    await page.getByTestId("create-country-name").fill(testName);
    await page.getByTestId("create-country-currency").fill("XZR");
    await page.getByTestId("create-country-timezone").fill("UTC");

    // Create
    await page.getByTestId("create-country-button").click();

    // Wait for the ledger to include the new entry
    await expect(page.getByTestId(`country-ledger-row-${testCode}`)).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText(/Created country/)).toBeVisible({ timeout: 10_000 });

    // Cleanup — deactivate test country (we leave it in the DB)
    await selectCountryFromLedger(page, testCode);
    // Go to overview tab
    await page.getByRole("button", { name: "Overview" }).click();
    const activeCheckbox = page.locator("label").filter({ hasText: "Active / Enabled" }).locator("input[type='checkbox']");
    if (await activeCheckbox.isChecked()) {
      await activeCheckbox.click();
      await page.getByRole("button", { name: "Update Identity" }).click();
      await expect(page.getByTestId("country-activity-message")).toContainText(/updated/i, { timeout: 15_000 });
    }
  });

  test("3. select country from ledger and verify overview tab loads", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    // Pick first available country
    const firstRow = page.getByTestId(/^country-ledger-row-/).first();
    await expect(firstRow).toBeVisible({ timeout: 30_000 });
    await firstRow.click();

    // Workspace should appear
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });

    // Overview tab fields should be populated
    const nameInput = page.locator("label").filter({ hasText: "Display Name" }).locator("input");
    await expect(nameInput).toBeVisible({ timeout: 10_000 });
  });

  test("4. tax preview and tax draft creation", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    // Select first country
    const firstRow = page.getByTestId(/^country-ledger-row-/).first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });

    // Navigate to Tax tab
    await page.getByRole("button", { name: "Tax & VAT" }).click();
    await expect(page.getByTestId("country-tax-panel")).toBeVisible({ timeout: 15_000 });

    // Fill tax preview
    const previewInput = page.locator("label").filter({ hasText: "Preview Price Amount" }).locator("input");
    await previewInput.fill("250");

    await page.getByTestId("preview-tax-button").click();
    await expect(page.getByTestId("tax-preview-result")).toBeVisible({ timeout: 30_000 });

    // Create draft
    await saveDraft(page, /Save Tax Draft/, /Tax draft created/i);
  });

  test("5. internal logistics draft creation", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.getByTestId(/^country-ledger-row-/).first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });

    await page.getByRole("button", { name: "Internal Logistics" }).click();
    await expect(page.getByTestId("country-logistics-panel")).toBeVisible({ timeout: 15_000 });

    await saveDraft(page, /Save Logistics Draft/, /Logistics draft created/i);
  });

  test("6. delivery partners — add provider and create draft", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.getByTestId(/^country-ledger-row-/).first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });

    await page.getByRole("button", { name: "Delivery Partners" }).click();

    // Add a test provider
    const providerIdInput = page.locator("label").filter({ hasText: "Provider ID" }).locator("input");
    const providerNameInput = page.locator("label").filter({ hasText: "Provider Name" }).locator("input");
    await providerIdInput.fill("test_provider");
    await providerNameInput.fill("Test Delivery Co");

    await page.getByRole("button", { name: "Add Integration Partner" }).click();
    await expect(page.getByText("Test Delivery Co")).toBeVisible({ timeout: 10_000 });

    await saveDraft(page, /Save Delivery Partners Draft/, /partners draft created/i);
  });

  test("7. payment gateways — add gateway and create draft", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.getByTestId(/^country-ledger-row-/).first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });

    await page.getByRole("button", { name: "Payment Gateways" }).click();

    // Add a test gateway
    const gwIdInput = page.locator("label").filter({ hasText: "Gateway ID" }).locator("input");
    const gwNameInput = page.locator("label").filter({ hasText: "Display Name" }).locator("input");
    await gwIdInput.fill("test_gw");
    await gwNameInput.fill("Test Gateway");

    await page.getByRole("button", { name: "Add Gateway Option" }).click();
    await expect(page.getByText("Test Gateway")).toBeVisible({ timeout: 10_000 });

    await saveDraft(page, /Save Payment Gateways Draft/, /gateways draft created/i);
  });

  test("8. legal rules draft creation", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.getByTestId(/^country-ledger-row-/).first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });

    await page.getByRole("button", { name: "Legal & Rules" }).click();

    await saveDraft(page, /Save Legal Rules Draft/, /legal rules draft created/i);
  });

  test("9. regions — add region and create draft", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.getByTestId(/^country-ledger-row-/).first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });

    await page.getByRole("button", { name: "Regions & Cities" }).click();

    // Add a region
    const regionInput = page.locator("label").filter({ hasText: "Region / Governorate Name" }).locator("input");
    const citiesInput = page.locator("label").filter({ hasText: "Cities (comma-separated list)" }).locator("input");
    await regionInput.fill("Test Region");
    await citiesInput.fill("City A, City B");

    await page.getByRole("button", { name: "Add Region Hub" }).click();
    await expect(page.getByText("Test Region")).toBeVisible({ timeout: 10_000 });

    await saveDraft(page, /Save Regions Draft/, /regions draft created/i);
  });

  test("10. supplier KYC draft creation", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.getByTestId(/^country-ledger-row-/).first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });

    await page.getByRole("button", { name: "Supplier KYC" }).click();

    // Toggle a document requirement
    const docCheckbox = page.locator("label").filter({ hasText: "Commercial Registration" }).locator("input[type='checkbox']");
    if (!(await docCheckbox.isChecked())) {
      await docCheckbox.check();
    }

    await saveDraft(page, /Save Supplier Rules Draft/, /supplier requirements draft created/i);
  });

  test("11. payout settings draft creation", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.getByTestId(/^country-ledger-row-/).first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });

    await page.getByRole("button", { name: "Payout Settings" }).click();

    await saveDraft(page, /Save Payout Settings Draft/, /payout settings draft created/i);
  });

  test("12. value commissions — add tier and create draft", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.getByTestId(/^country-ledger-row-/).first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });

    await page.getByRole("button", { name: "Value Commissions" }).click();

    // Add a commission tier
    const minInput = page.locator("label").filter({ hasText: "Min Order Value" }).locator("input");
    const pctInput = page.locator("label").filter({ hasText: "Commission Percentage" }).locator("input");
    await minInput.fill("0");
    await pctInput.fill("10");

    await page.getByRole("button", { name: "Add Value Tier" }).click();
    await expect(page.getByText("%")).toBeVisible({ timeout: 10_000 });

    await saveDraft(page, /Save Commission Tiers Draft/, /commission tiers draft created/i);
  });

  test("13. category commissions — add rate and create draft", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.getByTestId(/^country-ledger-row-/).first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });

    await page.getByRole("button", { name: "Category Commissions" }).click();
    await expect(page.getByTestId("country-commission-panel")).toBeVisible({ timeout: 15_000 });

    // Add a category rate
    const slugInput = page.locator("label").filter({ hasText: "Category Slug" }).locator("input");
    const rateInput = page.locator("label").filter({ hasText: "Commission Rate" }).locator("input");
    await slugInput.fill("test_category");
    await rateInput.fill("0.15");

    await page.getByRole("button", { name: "Add Category Rule" }).click();
    await expect(page.getByText("test_category")).toBeVisible({ timeout: 10_000 });

    await saveDraft(page, /Save Category Commissions Draft/, /category commissions draft created/i);
  });

  test("14. version history tab loads and shows entries", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.getByTestId(/^country-ledger-row-/).first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });

    // First create a tax draft so there is a version to see
    await page.getByRole("button", { name: "Tax & VAT" }).click();
    const previewInput = page.locator("label").filter({ hasText: "Preview Price Amount" }).locator("input");
    await previewInput.fill("100");
    await page.getByTestId("preview-tax-button").click();
    await page.getByTestId("create-tax-draft-button").click();
    await expect(page.getByTestId("country-activity-message")).toContainText(/Tax draft created/i, { timeout: 30_000 });

    // Navigate to Version History
    await page.getByRole("button", { name: "Version History" }).click();
    await expect(page.getByTestId("country-versions-panel")).toBeVisible({ timeout: 15_000 });

    const versionRow = page.locator("[data-version-id]").first();
    await expect(versionRow).toBeVisible({ timeout: 30_000 });
  });

});

