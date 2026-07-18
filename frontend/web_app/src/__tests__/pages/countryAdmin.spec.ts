import { test, expect } from "@playwright/test";

// Country Admin Workspace Tests
test.describe("Country Admin Workspace", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/admin/countries");
  });

  test("should display countries ledger with correct columns", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Countries Ledger" })).toBeVisible();
    await expect(page.getByTestId("ghost-country-form")).toBeVisible();
    
    // Check column headers
    await expect(page.getByText("Country")).toBeVisible();
    await expect(page.getByText("Code")).toBeVisible();
    await expect(page.getByText("Currency")).toBeVisible();
    await expect(page.getByText("Tax Rate")).toBeVisible();
  });

  test("should show ghost row for creating new country", async ({ page }) => {
    await page.getByTestId("ghost-country-form").waitFor({ state: "visible" });
    await expect(page.getByPlaceholder("AE")).toBeVisible();
    await expect(page.getByPlaceholder("United Arab Emirates")).toBeVisible();
  });

  test("should expand country row and show configuration workspace", async ({ page }) => {
    // First, create a country if none exists
    await page.getByPlaceholder("AE").fill("TEST");
    await page.getByPlaceholder("United Arab Emirates").fill("Test Country");
    await page.getByPlaceholder("AED").fill("AED");
    await page.getByPlaceholder("UTC").fill("UTC");
    await page.getByRole("button", { name: "Create Country" }).click();
    
    // Wait for the country to appear
    await page.waitForSelector("[data-testid='country-ledger-row-TEST']");
    
    // Click to expand
    await page.click("[data-testid='country-ledger-row-TEST']");
    
    // Check workspace elements
    await expect(page.getByTestId("country-config-workspace")).toBeVisible();
    await expect(page.getByRole("tab", { name: "Overview" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Tax & VAT" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Interactive Map" })).toBeVisible();
  });

  test("should have all 17 configuration tabs visible", async ({ page }) => {
    // Create test country
    await page.getByPlaceholder("AE").fill("TABTEST");
    await page.getByPlaceholder("United Arab Emirates").fill("Tab Test Country");
    await page.getByPlaceholder("AED").fill("AED");
    await page.getByPlaceholder("UTC").fill("UTC");
    await page.getByRole("button", { name: "Create Country" }).click();
    await page.waitForSelector("[data-testid='country-ledger-row-TABTEST']");
    await page.click("[data-testid='country-ledger-row-TABTEST']");
    
    // Check all tabs exist
    const expectedTabs = [
      "Overview", "Tax & VAT", "Internal Logistics", "Delivery Partners",
      "Payment Gateways", "Legal & Rules", "Regions & Cities", "Interactive Map",
      "Supplier KYC", "Payout Settings", "Value Commissions", "Category Commissions",
      "Feature Flags", "Analytics", "Staff Assignments", "Promotions", "Localization", "Version History"
    ];
    
    for (const tabName of expectedTabs) {
      await expect(page.getByRole("tab", { name: tabName })).toBeVisible();
    }
  });
});

// Tax Configuration Tests
test.describe("Tax & VAT Configuration", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/admin/countries");
    // Create test country
    await page.getByPlaceholder("AE").fill("TAXTEST");
    await page.getByPlaceholder("United Arab Emirates").fill("Tax Test");
    await page.getByPlaceholder("AED").fill("AED");
    await page.getByPlaceholder("UTC").fill("UTC");
    await page.getByRole("button", { name: "Create Country" }).click();
    await page.waitForSelector("[data-testid='country-ledger-row-TAXTEST']");
    await page.click("[data-testid='country-ledger-row-TAXTEST']");
    await page.getByRole("tab", { name: "Tax & VAT" }).click();
  });

  test("should have tax rate input with correct default", async ({ page }) => {
    const taxRateInput = page.getByLabel("Tax Rate (0 to 1)");
    await expect(taxRateInput).toHaveValue("0.15");
  });

  test("should show tax preview simulator", async ({ page }) => {
    await expect(page.getByLabel("Preview Price Amount")).toBeVisible();
    await expect(page.getByRole("button", { name: "Simulate VAT" })).toBeVisible();
  });

  test("should validate tax preview with valid amount", async ({ page }) => {
    await page.getByLabel("Preview Price Amount").fill("100");
    await page.getByRole("button", { name: "Simulate VAT" }).click();
    
    // Should show preview result
    await expect(page.getByText("Tax Applied:")).toBeVisible();
    await expect(page.getByText("Total Checkout Price:")).toBeVisible();
  });

  test("should create tax draft and show in versions", async ({ page }) => {
    await page.getByLabel("Tax Rate (0 to 1)").fill("0.10");
    await page.getByRole("button", { name: "Save Tax Draft" }).click();
    
    // Navigate to versions tab
    await page.getByRole("tab", { name: "Version History" }).click();
    await expect(page.getByText("Draft")).toBeVisible();
  });
});

// Interactive Map Tests
test.describe("Interactive Map Editor", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/admin/countries");
    await page.getByPlaceholder("AE").fill("MAPTEST");
    await page.getByPlaceholder("United Arab Emirates").fill("Map Test");
    await page.getByPlaceholder("AED").fill("AED");
    await page.getByPlaceholder("UTC").fill("UTC");
    await page.getByRole("button", { name: "Create Country" }).click();
    await page.waitForSelector("[data-testid='country-ledger-row-MAPTEST']");
    await page.click("[data-testid='country-ledger-row-MAPTEST']");
    await page.getByRole("tab", { name: "Interactive Map" }).click();
  });

  test("should display map container", async ({ page }) => {
    await expect(page.getByTestId("country-map")).toBeVisible();
  });

  test("should show empty state when no cities exist", async ({ page }) => {
    await expect(page.getByText("Click on the map to add cities")).toBeVisible();
  });

  test("should have search cities input", async ({ page }) => {
    await expect(page.getByPlaceholder("Search cities...")).toBeVisible();
  });

  test("should show add country button enabled", async ({ page }) => {
    await expect(page.getByRole("button", { name: "Add City" })).toBeVisible();
  });
});

// Commission Tiers Tests
test.describe("Commission Tiers Configuration", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/admin/countries");
    await page.getByPlaceholder("AE").fill("COMMTEST");
    await page.getByPlaceholder("United Arab Emirates").fill("Comm Test");
    await page.getByPlaceholder("AED").fill("AED");
    await page.getByPlaceholder("UTC").fill("UTC");
    await page.getByRole("button", { name: "Create Country" }).click();
    await page.waitForSelector("[data-testid='country-ledger-row-COMMTEST']");
    await page.click("[data-testid='country-ledger-row-COMMTEST']");
    await page.getByRole("tab", { name: "Value Commissions" }).click();
  });

  test("should display commission tiers editor", async ({ page }) => {
    await expect(page.getByText("Value-Based Commission Tiers")).toBeVisible();
    await expect(page.getByRole("button", { name: "Add Value Tier" })).toBeVisible();
  });

  test("should add new commission tier", async ({ page }) => {
    await page.getByLabel("Min Order Value").fill("0");
    await page.getByLabel("Commission Percentage").fill("5");
    await page.getByRole("button", { name: "Add Value Tier" }).click();
    
    await expect(page.getByText("0.00 AED - Unlimited")).toBeVisible();
    await expect(page.getByText("5%")).toBeVisible();
  });
});

// Role-Based Tab Visibility Tests
test.describe("Role-Based Tab Visibility", () => {
  test("country manager should see limited tabs", async ({ page }) => {
    // This test assumes a country_manager user is logged in
    await page.goto("/admin/countries");
    
    // Country managers should see fewer tabs
    const managerTabs = ["Overview", "Tax & VAT", "Internal Logistics", "Delivery Partners", 
                         "Payment Gateways", "Regions & Cities", "Value Commissions", "Category Commissions"];
    
    for (const tabName of managerTabs) {
      await expect(page.getByRole("tab", { name: tabName })).toBeVisible();
    }
  });
});

// Version History Tests
test.describe("Version History & Draft Workflow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/admin/countries");
    await page.getByPlaceholder("AE").fill("VERTEST");
    await page.getByPlaceholder("United Arab Emirates").fill("Version Test");
    await page.getByPlaceholder("AED").fill("AED");
    await page.getByPlaceholder("UTC").fill("UTC");
    await page.getByRole("button", { name: "Create Country" }).click();
    await page.waitForSelector("[data-testid='country-ledger-row-VERTEST']");
    await page.click("[data-testid='country-ledger-row-VERTEST']");
    await page.getByRole("tab", { name: "Version History" }).click();
  });

  test("should show version filter controls", async ({ page }) => {
    await expect(page.getByText("Filter By Config:")).toBeVisible();
    await expect(page.getByRole("button", { name: "All Configs" })).toBeVisible();
  });

  test("should show approve and publish buttons for drafts", async ({ page }) => {
    // Create a draft first
    await page.getByRole("tab", { name: "Tax & VAT" }).click();
    await page.getByRole("button", { name: "Save Tax Draft" }).click();
    
    // Go back to versions
    await page.getByRole("tab", { name: "Version History" }).click();
    
    // Find and click approve
    await page.waitForSelector("text/Draft");
    await page.getByRole("button", { name: "Approve" }).first().click();
    
    // Should show published state
    await expect(page.getByText("APPROVED")).toBeVisible();
  });
});
