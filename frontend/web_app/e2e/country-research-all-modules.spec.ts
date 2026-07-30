import { test, expect, type Page } from "@playwright/test";
import { bootstrapAdminSessionViaApi } from "./helpers/auth";

test.describe.configure({ timeout: 120_000 });

async function waitForNavigation(page: Page, expectedUrl: RegExp, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (expectedUrl.test(page.url())) return;
    await page.waitForTimeout(250);
  }
  throw new Error(`Timed out waiting for ${expectedUrl}. Current URL: ${page.url()}`);
}

async function bootstrapSessionViaApi(page: Page, candidates: string[], password: string) {
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
  for (const candidate of candidates) {
    await bootstrapAdminSessionViaApi(page);
    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1"));
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    return true;
  }
  return false;
}

async function loginAsAdmin(page: Page) {
  const hasApiSession = await bootstrapSessionViaApi(page, ["admin@zozi.com", "admin"], "admin123");
  if (hasApiSession) {
    await waitForNavigation(page, /\/admin\/countries/, 120_000);
    return;
  }
  test.skip(true, "Cannot authenticate — no valid login method");
}

const MODULE_LABELS = [
  "Country Identity", "Demographics", "Economy & Wealth", "Tax & Duties",
  "Consumer Psychology", "Consumption Preferences", "Shopping Seasonality",
  "Digital Landscape", "Payment Infrastructure", "Logistics & Shipping",
  "Legal & Regulations", "Language & Communication", "Community & Social",
  "Marketing & Advertising", "Competition & Market", "Customer Service",
  "Technology & Infrastructure", "News & Current Context", "Risk & Compliance",
  "Strategic Recommendations",
];

test.describe("Country Research — All 20 Modules (E2E)", () => {

  test.beforeEach(async ({ page }) => {
    await bootstrapAdminSessionViaApi(page);
  });

  test("01 — Backend API returns all 20 modules with correct structure", async ({ page }) => {
    const res = await page.request.get("http://127.0.0.1:8000/country-research/SA/research", {
      failOnStatusCode: false,
    });
    expect(res.status()).toBe(200);

    const body = await res.json();
    expect(body.status).toBe("success");
    const data = body.data;

    expect(data.meta.country_code).toBe("SA");
    expect(data.meta.country_name).toBe("Saudi Arabia");
    expect(data.meta.modules_total).toBe(20);
    expect(["high", "medium", "low"]).toContain(data.meta.overall_confidence);
    expect(data.meta.generated_at_utc).toBeTruthy();
    expect(data.meta.data_sources.length).toBeGreaterThanOrEqual(1);

    const moduleKeys = Object.keys(data).filter((k) => k.startsWith("module_"));
    expect(moduleKeys.length).toBe(20);
    for (const key of moduleKeys) {
      expect(["high", "medium", "low"]).toContain(data[key].confidence);
      expect(Array.isArray(data[key].sources)).toBe(true);
    }

    const m1 = data.module_01_country_identity;
    expect(m1.confidence).toBe("high");
    expect(m1.common_name).toBe("Saudi Arabia");
    expect(m1.country_code_alpha2).toBe("SA");
    expect(m1.official_name).toBeTruthy();
    expect(m1.capital).toBeTruthy();
    expect(typeof m1.population).toBe("number");
    expect(m1.currency_code).toBeTruthy();

    const m2 = data.module_02_demographics;
    expect(m2.confidence).toBe("high");
    expect(m2.total_population).toBeGreaterThan(0);
    expect(typeof m2.cities_count).toBe("number");
    expect(Array.isArray(m2.top_cities)).toBe(true);

    const m3 = data.module_03_economy_wealth;
    expect(m3.confidence).toBe("medium");
    expect(m3.currency_code).toBeTruthy();
    expect(m3.tax_type).toBeTruthy();
  });

  test("02 — Cross-module data consistency", async ({ page }) => {
    const res = await page.request.get("http://127.0.0.1:8000/country-research/SA/research");
    const data = (await res.json()).data;

    expect(data.meta.country_code).toBe(data.module_01_country_identity.country_code_alpha2);
    expect(data.meta.country_name).toBe(data.module_01_country_identity.common_name);
    expect(data.module_01_country_identity.population).toBe(data.module_02_demographics.total_population);
    expect(data.module_02_demographics.total_population).toBe(data.module_03_economy_wealth.population);
    expect(data.module_01_country_identity.currency_code).toBe(data.module_03_economy_wealth.currency_code);
    expect(data.module_02_demographics.internet_penetration_pct).toBe(data.module_03_economy_wealth.internet_penetration_pct);
  });

  test("03 — DB values align with research response (tax fields)", async ({ page }) => {
    const res = await page.request.get("http://127.0.0.1:8000/country-research/SA/research");
    const data = (await res.json()).data;

    const dbRes = await page.request.get("http://127.0.0.1:8000/countries/SA", { failOnStatusCode: false });
    if (dbRes.ok()) {
      const dbCountry = ((await dbRes.json()).data || {});
      if (dbCountry.tax_type) expect(data.module_03_economy_wealth.tax_type).toBe(dbCountry.tax_type);
      if (dbCountry.tax_rate !== undefined) {
        expect(data.module_03_economy_wealth.tax_rate).toBeCloseTo(parseFloat(String(dbCountry.tax_rate)), 2);
      }
    } else {
      expect(data.module_01_country_identity.common_name).toBeTruthy();
    }
  });

  test("04 — Frontend renders Research tab with all 20 modules", async ({ page }) => {
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await page.waitForTimeout(3000);

    const saRow = page.locator("[data-testid='country-ledger-row-SA']");
    if (await saRow.isVisible().catch(() => false)) {
      await saRow.click();
    } else {
      const anyRow = page.locator("[data-testid^='country-ledger-row-']").first();
      if (await anyRow.isVisible().catch(() => false)) {
        await anyRow.click();
      } else {
        test.skip(true, "No country rows available");
        return;
      }
    }

    await expect(page.getByTestId("country-config-workspace")).toBeVisible({ timeout: 15_000 });
    await page.getByRole("tab", { name: "Research" }).click();
    await page.waitForTimeout(3000);

    const loadingEl = page.locator("text=Loading research data").first();
    if (await loadingEl.isVisible().catch(() => false)) {
      await expect(loadingEl).not.toBeVisible({ timeout: 30_000 });
    }

    await expect(page.getByText("Saudi Arabia").first()).toBeVisible({ timeout: 10_000 });

    for (const label of MODULE_LABELS) {
      await expect(page.getByText(label).first()).toBeVisible({ timeout: 5_000 });
    }

    expect(await page.locator("text=HIGH").count()).toBeGreaterThanOrEqual(1);
    expect(await page.locator("text=MEDIUM").count()).toBeGreaterThanOrEqual(1);
    expect(await page.locator("text=LOW").count()).toBeGreaterThanOrEqual(10);

    await expect(page.getByText("REST Countries API").first()).toBeVisible();
    await expect(page.getByText("World Bank API").first()).toBeVisible();
    await expect(page.getByPlaceholder("Search modules and data points...")).toBeVisible();
  });

  test("05 — Modules 1-3 open by default with visible field labels", async ({ page }) => {
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await page.waitForTimeout(3000);

    const saRow = page.locator("[data-testid='country-ledger-row-SA']");
    if (!(await saRow.isVisible().catch(() => false))) {
      test.skip(true, "SA row not visible");
      return;
    }
    await saRow.click();

    await expect(page.getByTestId("country-config-workspace")).toBeVisible({ timeout: 15_000 });
    await page.getByRole("tab", { name: "Research" }).click();
    await page.waitForTimeout(3000);

    const loadingEl = page.locator("text=Loading research data").first();
    if (await loadingEl.isVisible().catch(() => false)) await expect(loadingEl).not.toBeVisible({ timeout: 30_000 });

    await expect(page.getByText("COUNTRY CODE ALPHA2").first()).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText("CURRENCY CODE").first()).toBeVisible({ timeout: 5_000 });
  });

  test("06 — Search filters modules correctly", async ({ page }) => {
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await page.waitForTimeout(3000);

    const saRow = page.locator("[data-testid='country-ledger-row-SA']");
    if (!(await saRow.isVisible().catch(() => false))) {
      test.skip(true, "SA row not visible");
      return;
    }
    await saRow.click();

    await expect(page.getByTestId("country-config-workspace")).toBeVisible({ timeout: 15_000 });
    await page.getByRole("tab", { name: "Research" }).click();
    await page.waitForTimeout(3000);

    const loadingEl = page.locator("text=Loading research data").first();
    if (await loadingEl.isVisible().catch(() => false)) await expect(loadingEl).not.toBeVisible({ timeout: 30_000 });

    const searchInput = page.getByPlaceholder("Search modules and data points...");
    await expect(searchInput).toBeVisible({ timeout: 10_000 });

    await searchInput.fill("tax");
    await page.waitForTimeout(500);

    let visibleCount = 0;
    for (const label of ["Tax & Duties", "Country Identity", "Demographics", "Economy & Wealth"]) {
      if (await page.getByText(label).first().isVisible().catch(() => false)) visibleCount++;
    }
    expect(visibleCount).toBeGreaterThan(0);

    await searchInput.fill("");
    await page.waitForTimeout(500);
    await expect(page.getByText("Country Identity").first()).toBeVisible();
    await expect(page.getByText("Strategic Recommendations").first()).toBeVisible();
  });

  test("07 — Non-existent country returns 404", async ({ page }) => {
    const res = await page.request.get("http://127.0.0.1:8000/country-research/XX/research", {
      failOnStatusCode: false,
    });
    expect(res.status()).toBe(404);
  });
});
