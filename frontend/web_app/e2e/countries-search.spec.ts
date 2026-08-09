// Playwright test: verify "search a country" auto-populate works on /admin/countries.
//
// Regression coverage for the country-search contract:
//   - POST /admin/countries/auto-populate accepts { search_term } in the JSON body
//     and returns an UNWRAPPED country payload (code/name/currency/.../suggested_*).
//   - The GhostRowForm "Auto-populate from web" panel is wired to that endpoint and
//     fills the quick-create form fields when a country is searched.
//
// Uses the same proven login helper conventions as admin-country-enhanced.spec.ts.

import { test, expect, type Page } from "@playwright/test";
import { bootstrapAdminSessionViaApi } from "./helpers/auth";

const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:3000";

async function waitForAdminNavigation(page: Page, expectedUrl: RegExp, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (expectedUrl.test(page.url())) return;
    await page.waitForTimeout(250);
  }
  throw new Error(`Timed out waiting for ${expectedUrl}. Current URL: ${page.url()}`);
}

async function loginAsAdmin(page: Page, destination = "/admin/countries") {
  for (const candidate of ["admin@zozi.com", "admin"]) {
    await bootstrapAdminSessionViaApi(page);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page
      .evaluate(() => window.localStorage.setItem("zozi_has_session", "1"))
      .catch(() => undefined);
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    await waitForAdminNavigation(page, /\/admin\/(dashboard|countries)(?:\?|$)/, 120_000);
    if (await page.getByRole("heading", { name: /Admin Access/i }).first().isVisible().catch(() => false)) {
      continue;
    }
    await page.goto(destination, { waitUntil: "domcontentloaded" });
    return;
  }
  // Fallback to the on-page login form.
  await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
  const submit = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await submit.waitFor();
  const form = submit.locator("xpath=ancestor::form[1]");
  const identifier = form
    .locator("input[name='username']:visible")
    .or(form.locator("input[autocomplete='username']:visible"))
    .or(form.locator("input[required]:not([type='password']):visible"))
    .first();
  await identifier.fill("admin@zozi.com");
  await form.locator("input[type='password']:visible").first().fill("admin123");
  await submit.click();
  await waitForAdminNavigation(page, /\/admin\/countries(?:\?|$)/, 120_000);
}

test.describe("Admin Countries — country search / auto-populate", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");
  });

  test("country search panel is wired in the quick-create form", async ({ page }) => {
    await page.getByTestId("add-country-button").click();
    await expect(page.getByTestId("new-country-modal")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Auto-populate from web")).toBeVisible();
    const searchInput = page.getByTestId("auto-populate-search-input");
    await expect(searchInput).toBeVisible();
  });

  test("searching a country populates the quick-create form", async ({ page }) => {
    await page.getByTestId("add-country-button").click();
    await expect(page.getByTestId("new-country-modal")).toBeVisible({ timeout: 10_000 });

    const searchInput = page.getByTestId("auto-populate-search-input");
    await searchInput.fill("Saudi Arabia");
    await page.getByRole("button", { name: "Search" }).click();

    // The auto-populate call fills the ghost form fields.
    const codeInput = page.getByTestId("ghost-code-input");
    await expect(codeInput).toHaveValue("SA", { timeout: 20_000 });

    const nameInput = page.getByTestId("ghost-name-input");
    await expect(nameInput).toHaveValue("Saudi Arabia", { timeout: 20_000 });

    // Close the form.
    await page.getByRole("button", { name: "Cancel" }).click();
    await expect(page.getByTestId("new-country-modal")).not.toBeVisible({ timeout: 5_000 });
  });
});

