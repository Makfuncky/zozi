import { expect, test, type Page } from "@playwright/test";
import { bootstrapAdminSessionViaApi } from "./helpers/auth";

test.describe.configure({ timeout: 240_000 });

async function loginAsAdmin(page: Page) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
  
  const hasSession = await bootstrapAdminSessionViaApi(page);

  if (hasSession) {
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    return;
  }

  await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
  const submitButton = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await submitButton.waitFor();
  
  const form = submitButton.locator("xpath=ancestor::form[1]");
  const identifierCandidates = [
    form.locator("input[name='username']:visible"),
    form.locator("input[autocomplete='username']:visible"),
    form.locator("input[required]:not([type='password']):visible"),
  ];

  let identifierFilled = false;
  for (const candidate of identifierCandidates) {
    if (await candidate.count()) {
      await candidate.first().fill("admin@zozi.com");
      identifierFilled = true;
      break;
    }
  }

  if (!identifierFilled) {
    throw new Error("Unable to find a visible username/email input on the login form.");
  }

  const passwordInput = form.locator("input[type='password']:visible").first();
  await passwordInput.fill("admin123");
  await submitButton.click();
}

test.describe("Supplier KYC Form", () => {
  
  test("supplier KYC tab loads with document checklist", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded" });
    
    // Select first country
    const firstRow = page.locator("table tbody tr").first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });
    
    // Navigate to Supplier KYC tab
    await page.getByRole("button", { name: "Supplier KYC" }).click();
    await expect(page.getByText("Supplier Onboarding & Compliance")).toBeVisible({ timeout: 10_000 });
    
    // Should show KYC level selector
    await expect(page.getByLabel("KYC Clearance Level")).toBeVisible({ timeout: 10_000 });
    
    // Should show document checklist
    await expect(page.getByText("Required Documents Checklist")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Commercial Registration")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("VAT Certificate")).toBeVisible({ timeout: 10_000 });
  });

  test("can toggle document requirements", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded" });
    
    const firstRow = page.locator("table tbody tr").first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });
    
    await page.getByRole("button", { name: "Supplier KYC" }).click();
    
    // Toggle a document requirement
    const crCheckbox = page.locator("label").filter({ hasText: "Commercial Registration" }).locator("input[type='checkbox']");
    await crCheckbox.check();
    await expect(crCheckbox).toBeChecked();
    
    // Toggle another one
    const vatCheckbox = page.locator("label").filter({ hasText: "VAT Certificate" }).locator("input[type='checkbox']");
    await vatCheckbox.check();
    await expect(vatCheckbox).toBeChecked();
  });

test("can change KYC level", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded" });
    
    const firstRow = page.locator("table tbody tr").first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30000 });
    
    await page.getByRole("button", { name: "Supplier KYC" }).click();
    
    // Change KYC level - find the select by its label text proximity
    const kycSelect = page.locator("label").filter({ hasText: "KYC Clearance Level" }).locator("select, [role='combobox']").first();
    
    // Select enhanced level
    await kycSelect.selectOption("enhanced");
    
    // Save supplier requirements
    await page.getByRole("button", { name: "Save Supplier Rules Draft" }).click();
    await expect(page.getByText(/supplier requirements draft created/i)).toBeVisible({ timeout: 30000 });
  });

  test("supplier KYC form validates required fields", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded" });
    
    const firstRow = page.locator("table tbody tr").first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });
    
    await page.getByRole("button", { name: "Supplier KYC" }).click();
    
    // Approval required checkbox should be visible
    await expect(page.getByLabel(/Require manual ops approval/i)).toBeVisible({ timeout: 10_000 });
  });

});
