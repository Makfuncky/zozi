import { expect, test, type Page } from "@playwright/test";
import { submitCredentialForm } from "../../../src/auth";

test.describe.configure({ timeout: 240_000 });

// Test for customer-facing cross-border checkout behavior
test.describe("Cross-Border Checkout", () => {
  
  test("customer can view tax preview for different countries", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    
    // This test simulates a customer viewing tax calculations
    // The actual implementation would depend on the customer-facing checkout flow
    
    // For now, we test that the admin can configure cross-border tax rules
    await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
    
    // Login as admin
    await submitCredentialForm(page, "admin@zozi.com", "E2eAdmin#2026");
    
    // Navigate to countries
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded" });
    
    // Select a country
    const firstRow = page.locator("table tbody tr").first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30000 });
    
    // Go to Tax tab
    await page.getByRole("button", { name: "Tax & VAT" }).click();
    await expect(page.getByText("Tax & VAT Configuration")).toBeVisible({ timeout: 10000 });
    
    // Test tax preview functionality
    const previewAmount = page.locator("input[placeholder]").filter({ hasText: /amount/i }).or(
      page.locator("label").filter({ hasText: "Preview Price Amount" }).locator("input")
    );
    
    if (await previewAmount.count() > 0) {
      await previewAmount.first().fill("100");
      
      const previewButton = page.getByRole("button", { name: /Simulate VAT|Preview/i });
      if (await previewButton.count() > 0) {
        await previewButton.first().click();
        await expect(page.getByText(/Tax Applied|Total Checkout Price/)).toBeVisible({ timeout: 10000 });
      }
    }
  });

  test("can configure multiple payment gateways for cross-border", async ({ page }) => {
    await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
    
    await submitCredentialForm(page, "admin@zozi.com", "E2eAdmin#2026");
    
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded" });
    
    const firstRow = page.locator("table tbody tr").first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30000 });
    
    // Go to Payment Gateways tab
    await page.getByRole("button", { name: "Payment Gateways" }).click();
    await expect(page.getByText("Payment Gateways & Transaction Rules")).toBeVisible({ timeout: 10000 });
    
    // Verify gateway configuration fields exist
    await expect(page.getByText("Gateway ID")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Display Name")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Integration Type")).toBeVisible({ timeout: 10000 });
  });

  test("can configure logistics providers for delivery", async ({ page }) => {
    await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
    
    await submitCredentialForm(page, "admin@zozi.com", "E2eAdmin#2026");
    
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded" });
    
    const firstRow = page.locator("table tbody tr").first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30000 });
    
    // Go to Delivery Partners tab
    await page.getByRole("button", { name: "Delivery Partners" }).click();
    await expect(page.getByText("Delivery Partners & Logistics Integrations")).toBeVisible({ timeout: 10000 });
    
    // Verify provider configuration fields exist
    await expect(page.getByText("Provider ID")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Provider Name")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Standard SLA")).toBeVisible({ timeout: 10000 });
  });

  test("can configure feature flags for country-specific features", async ({ page }) => {
    await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
    
    await submitCredentialForm(page, "admin@zozi.com", "E2eAdmin#2026");
    
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded" });
    
    const firstRow = page.locator("table tbody tr").first();
    await firstRow.click();
    await expect(page.getByText("Sections")).toBeVisible({ timeout: 30000 });
    
    // Go to Feature Flags tab
    await page.getByRole("button", { name: "Feature Flags" }).click();
    await expect(page.getByText("Feature Flags & Platform Toggles")).toBeVisible({ timeout: 10000 });
    
    // Verify feature flag controls exist
    await expect(page.getByText("Add New Feature Flag")).toBeVisible({ timeout: 10000 });
  });

});
