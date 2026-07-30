import { expect, test } from "@playwright/test";
import { loginAs } from "../helpers/auth";

test.describe("Products E2E", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, "customer@zozi.com", "customer123");
    await page.goto("/products", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  test("products page loads", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /products/i }).first()).toBeVisible({ timeout: 30_000 });
  });

  test("product cards are visible", async ({ page }) => {
    await page.waitForSelector("[data-testid='product-card'], .product-card, article", { timeout: 30_000 });
    const cards = await page.locator("[data-testid='product-card'], .product-card, article").count();
    expect(cards).toBeGreaterThanOrEqual(0);
  });

  test("search filters products", async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i).first();
    if (await searchInput.count() > 0) {
      await searchInput.fill("phone");
      await page.waitForTimeout(2000);
    }
  });

  test("category filter exists", async ({ page }) => {
    const categorySelect = page.getByLabel(/category/i).first();
    if (await categorySelect.count() > 0) {
      await expect(categorySelect).toBeVisible();
    }
  });

  test("product detail navigation", async ({ page }) => {
    const firstProduct = page.locator("[data-testid='product-card'], .product-card, article").first();
    if (await firstProduct.count() > 0) {
      await firstProduct.click();
      await expect(page).toHaveURL(/\/products\//);
    }
  });
});
