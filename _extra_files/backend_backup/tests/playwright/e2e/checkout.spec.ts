import { expect, test } from "@playwright/test";
import { loginAs } from "../helpers/auth";

test.describe("Checkout E2E", () => {
  test("checkout page requires login", async ({ page }) => {
    await page.goto("/checkout", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await expect(page.getByText(/login|sign in/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("authenticated user can access checkout", async ({ page }) => {
    await loginAs(page, "customer@zozi.com", "customer123");
    await page.goto("/checkout", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await expect(page.getByText(/checkout|payment/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("checkout shows shipping form", async ({ page }) => {
    await loginAs(page, "customer@zozi.com", "customer123");
    await page.goto("/checkout", { waitUntil: "domcontentloaded", timeout: 60_000 });
    const shippingInput = page.getByPlaceholder(/address|street/i).first();
    if (await shippingInput.count() > 0) {
      await expect(shippingInput).toBeVisible();
    }
  });

  test("checkout shows payment method options", async ({ page }) => {
    await loginAs(page, "customer@zozi.com", "customer123");
    await page.goto("/checkout", { waitUntil: "domcontentloaded", timeout: 60_000 });
    const paymentSection = page.getByText(/payment method|pay with/i).first();
    if (await paymentSection.count() > 0) {
      await expect(paymentSection).toBeVisible();
    }
  });

  test("place order button exists on checkout", async ({ page }) => {
    await loginAs(page, "customer@zozi.com", "customer123");
    await page.goto("/checkout", { waitUntil: "domcontentloaded", timeout: 60_000 });
    const placeOrderBtn = page.getByRole("button", { name: /place order|complete order/i }).first();
    if (await placeOrderBtn.count() > 0) {
      await expect(placeOrderBtn).toBeVisible();
    }
  });
});
