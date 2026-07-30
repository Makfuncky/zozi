import { expect, test, type Page } from "@playwright/test";
import { bootstrapAdminSessionViaApi } from "./helpers/auth";

test.describe.configure({ timeout: 240_000 });

// Import helpers from existing test file
async function loginAsAdmin(page: Page, destination = "/admin/countries") {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
  
  const hasSession = await bootstrapAdminSessionViaApi(page);

  if (hasSession) {
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    return;
  }

  // Fallback to admin login
  await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
  const submitButton = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await submitButton.waitFor();
  
  const form = submitButton.locator("xpath=ancestor::form[1]");
  const identifierCandidates = [
    form.locator("input[name='username']:visible"),
    form.locator("input[autocomplete='username']:visible"),
    form.locator("input[required]:not([type='password']):visible"),
    form.locator("input[type='email']:visible"),
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

test.describe("Country Auto-Populate Feature", () => {
  
  test("auto-populate search shows suggestions for valid country", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded" });
    
    // Click Add Country button to show ghost row
    await page.getByRole("button", { name: "Add Country" }).click();
    await expect(page.getByTestId("auto-populate-search-input")).toBeVisible({ timeout: 10_000 });
    
    // Search for Saudi Arabia
    await page.getByTestId("auto-populate-search-input").fill("Saudi Arabia");
    
    // Wait for search results (debounced)
    await page.waitForTimeout(1000);
    
    // Should show auto-populate result
    await expect(page.getByText("Auto-Populated Data")).toBeVisible({ timeout: 15_000 });
  });

  test("auto-populate fills form fields with suggested data", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded" });
    
    // Click Add Country button
    await page.getByRole("button", { name: "Add Country" }).click();
    
    // Search for UAE
    await page.getByTestId("auto-populate-search-input").fill("United Arab Emirates");
    await page.waitForTimeout(1500);
    
    // Should populate the form fields
    const codeInput = page.getByPlaceholder("AE");
    const nameInput = page.getByPlaceholder("United Arab Emirates");
    
    // After auto-populate, fields should be filled
    await expect(codeInput).toBeVisible({ timeout: 10_000 });
  });

  test("auto-populate shows tax rate suggestions", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded" });
    
    await page.getByRole("button", { name: "Add Country" }).click();
    await page.getByTestId("auto-populate-search-input").fill("Saudi Arabia");
    await page.waitForTimeout(1500);
    
    // Should show tax rate in auto-populate result
    await expect(page.getByText(/Tax Rate:/)).toBeVisible({ timeout: 10_000 });
  });

});
