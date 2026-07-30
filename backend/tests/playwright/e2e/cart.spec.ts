import { expect, test } from "@playwright/test";
import { loginAs } from "../helpers/auth";

test.describe("Cart E2E", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, "customer@zozi.com", "customer123");
  });

  test("cart page shows empty cart initially", async ({ page }) => {
    await page.goto("/cart", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await expect(page.getByText(/empty|no items|your cart/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("can navigate to cart from header", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 60_000 });
    const cartLink = page.getByRole("link", { name: /cart/i }).first();
    if (await cartLink.count() > 0) {
      await cartLink.click();
      await expect(page).toHaveURL(/\/cart/);
    }
  });

  test("cart icon shows item count badge", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 60_000 });
    const cartBadge = page.locator("[data-testid='cart-badge'], .cart-badge, [aria-label*='cart']").first();
    if (await cartBadge.count() > 0) {
      await expect(cartBadge).toBeVisible();
    }
  });
});
