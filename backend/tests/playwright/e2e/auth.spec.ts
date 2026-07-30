import { expect, test } from "@playwright/test";
import { loginAs } from "../helpers/auth";

test.describe("Authentication E2E", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/auth/login", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  test("displays login form", async ({ page }) => {
    await expect(page.getByText(/sign in|log in|signin/i).first()).toBeVisible();
  });

  test("customer can login", async ({ page }) => {
    await loginAs(page, "customer@zozi.com", "customer123");
    await expect(page).toHaveURL(/\/(?:$|\?)/);
  });

  test("supplier can login", async ({ page }) => {
    await loginAs(page, "supplier@zozi.com", "supplier123");
    await expect(page).toHaveURL(/\/(?:$|\?)/);
  });

  test("admin can login", async ({ page }) => {
    await loginAs(page, "admin@zozi.com", "admin123");
    await expect(page).toHaveURL(/\/(?:$|\?)/);
  });

  test("shows error on wrong password", async ({ page }) => {
    await page.locator("input[type='email']").first().fill("customer@zozi.com");
    await page.locator("input[type='password']").first().fill("wrongpassword");
    await page.getByRole("button", { name: /sign in|log in|signin/i }).first().click();
    await expect(page.getByText(/invalid credentials|incorrect|error/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("shows error on missing credentials", async ({ page }) => {
    await page.getByRole("button", { name: /sign in|log in|signin/i }).first().click();
    await expect(page.getByText(/required|fill/i).first()).toBeVisible({ timeout: 15_000 });
  });
});
