import { expect, test } from "@playwright/test";
import { loginAs } from "../helpers/auth";

test.describe("User Profile E2E", () => {
  test("profile page shows user info", async ({ page }) => {
    await loginAs(page, "customer@zozi.com", "customer123");
    await page.goto("/profile", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await expect(page.getByText(/profile|account/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("orders page shows order history", async ({ page }) => {
    await loginAs(page, "customer@zozi.com", "customer123");
    await page.goto("/orders", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await expect(page.getByText(/orders|order history/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("wishlist page loads", async ({ page }) => {
    await loginAs(page, "customer@zozi.com", "customer123");
    await page.goto("/wishlist", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await expect(page.getByText(/wishlist|saved items/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("notifications page loads", async ({ page }) => {
    await loginAs(page, "customer@zozi.com", "customer123");
    await page.goto("/notifications", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await expect(page.getByText(/notifications/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("returns page loads", async ({ page }) => {
    await loginAs(page, "customer@zozi.com", "customer123");
    await page.goto("/returns", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await expect(page.getByText(/returns/i).first()).toBeVisible({ timeout: 30_000 });
  });
});
