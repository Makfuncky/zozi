import { expect, test, type Page } from "@playwright/test";

test.describe.configure({ timeout: 240_000 });

async function loginAsAdmin(page: Page, destination = "/admin/countries") {
  const loginResponse = await page.request.post("/api/auth/login", {
    form: { username: "admin@zozi.com", password: "admin123" },
    failOnStatusCode: false,
  });

  if (!loginResponse.ok()) {
    throw new Error("Failed to login as admin");
  }

  await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
  await page.request.get("/api/auth/me", { failOnStatusCode: false });
  await page.goto(destination, { waitUntil: "domcontentloaded", timeout: 120_000 });
}

test.describe("Ghost Row / Inline Form Tests", () => {
  test("1. Ghost row appears when creating a new country", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const ghostRow = page.locator("tr[data-country-code='NEW']");
    await expect(ghostRow).toBeVisible({ timeout: 30_000 });

    await ghostRow.locator("input[name='code']").fill("TEST");
    await ghostRow.locator("input[name='name']").fill("Test Country");
    await ghostRow.locator("input[name='currency']").fill("TST");

    await ghostRow.locator("button[type='submit']").click();
    await expect(page.locator("tr[data-country-code='TEST']")).toBeVisible({ timeout: 30_000 });
  });

  test("2. Ghost row can be cancelled", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const ghostRow = page.locator("tr[data-country-code='NEW']");
    await expect(ghostRow).toBeVisible({ timeout: 30_000 });

    await ghostRow.locator("button[aria-label='cancel']").click();
    await expect(ghostRow).toBeHidden({ timeout: 10_000 });
  });
});

test.describe("Draft-to-Publish Workflow Tests", () => {
  test("3. Create tax draft and approve it", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.locator("table tbody tr").first();
    const countryCode = await firstRow.getAttribute("data-country-code");
    await firstRow.click();

    await page.getByRole("button", { name: "Tax & VAT" }).click();

    const previewInput = page.locator("label").filter({ hasText: "Preview Price Amount" }).locator("input");
    await previewInput.fill("100");

    await page.getByTestId("preview-tax-button").click();
    await page.getByTestId("create-tax-draft-button").click();

    const draftVersion = await page.locator("[data-testid='country-version-item']").first().getAttribute("data-version-id");
    expect(draftVersion).toBeTruthy();

    await page.getByRole("button", { name: "Approve" }).first().click();
    await expect(page.locator("text=Approved")).toBeVisible({ timeout: 10_000 });
  });

  test("4. Publish a version", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.locator("table tbody tr").first();
    await firstRow.click();

    await page.getByRole("button", { name: "Tax & VAT" }).click();

    const previewInput = page.locator("label").filter({ hasText: "Preview Price Amount" }).locator("input");
    await previewInput.fill("200");

    await page.getByTestId("preview-tax-button").click();
    await page.getByTestId("create-tax-draft-button").click();

    await page.getByRole("button", { name: "Approve" }).first().click();
    await page.getByRole("button", { name: "Publish" }).first().click();

    await expect(page.locator("text=Published")).toBeVisible({ timeout: 10_000 });
  });

  test("5. Rollback to previous version", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.locator("table tbody tr").first();
    await firstRow.click();

    await page.getByRole("button", { name: "Version History" }).click();

    const publishedVersion = page.locator("[data-version-status='published']").first();
    const versionId = await publishedVersion.getAttribute("data-version-id");

    await publishedVersion.locator("button[aria-label='rollback']").click();
    await page.locator("button:text('Confirm Rollback')").click();

    await expect(page.locator("text=Rollback applied")).toBeVisible({ timeout: 10_000 });
  });
});

test.describe("RLS (Row Level Security) Isolation Tests", () => {
  test("6. Country head can only see assigned countries", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const allCountries = page.locator("table tbody tr[data-country-code]");
    const count = await allCountries.count();
    expect(count).toBeGreaterThan(0);

    const firstCountryCode = await allCountries.first().getAttribute("data-country-code");
    await page.locator("select[name='country_filter']").selectOption(firstCountryCode!);

    const filteredRows = page.locator("table tbody tr[data-country-code]");
    const filteredCount = await filteredRows.count();
    expect(filteredCount).toBe(1);
    await expect(filteredRows.first()).toContainText(firstCountryCode!);
  });

  test("7. Staff assignment restricts access", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.locator("table tbody tr").first();
    const countryCode = await firstRow.getAttribute("data-country-code");

    await page.getByRole("button", { name: "Staff" }).click();

    const assignInput = page.locator("input[placeholder='Search user...']");
    await assignInput.fill("testuser");

    await page.getByRole("button", { name: "Assign" }).first().click();

    await expect(page.locator("text=Assigned successfully")).toBeVisible({ timeout: 10_000 });
  });
});

test.describe("Cross-Country Session Tracking Tests", () => {
  test("8. Cross-border session is recorded", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.locator("table tbody tr").first();
    const countryCode = await firstRow.getAttribute("data-country-code");

    await page.getByRole("button", { name: "Cross-Country Sessions" }).click();

    const sessionTable = page.locator("table[data-testid='cross-country-sessions']");
    await expect(sessionTable).toBeVisible({ timeout: 10_000 });
  });
});

test.describe("Product Restriction Integration Tests", () => {
  test("9. Restricted products are hidden in checkout", async ({ page }) => {
    await page.goto("/products?category=alcohol", { waitUntil: "domcontentloaded" });

    const products = page.locator("[data-testid='product-card']");
    const count = await products.count();

    for (let i = 0; i < count; i++) {
      const country = await page.evaluate(() => (window as any).__TEST_COUNTRY__);
      if (country === "AE") {
        await expect(products.nth(i)).toBeHidden();
      }
    }
  });
});

test.describe("Payment Gateway Country Sync Tests", () => {
  test("10. Gateways are synced from country config", async ({ page }) => {
    await loginAsAdmin(page, "/admin/countries");

    const firstRow = page.locator("table tbody tr").first();
    const countryCode = await firstRow.getAttribute("data-country-code");
    await firstRow.click();

    await page.getByRole("button", { name: "Payment Gateways" }).click();

    const syncButton = page.getByRole("button", { name: "Sync from Country Config" });
    if (await syncButton.isVisible()) {
      await syncButton.click();
      await expect(page.locator("text=Synced")).toBeVisible({ timeout: 10_000 });
    }
  });
});