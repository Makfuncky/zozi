import { test, expect } from '@playwright/test';

const BASE = process.env.PW_BASE_URL || 'http://localhost:8090';

test.describe('Navigation and Deep Routes', () => {
  test('wishlist page loads', async ({ page }) => {
    await page.goto(`${BASE}/wishlist`);
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toBeVisible();
  });

  test('notifications page loads', async ({ page }) => {
    await page.goto(`${BASE}/notifications`);
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toBeVisible();
  });

  test('offers page loads', async ({ page }) => {
    await page.goto(`${BASE}/offers`);
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toBeVisible();
  });

  test('flash sales page loads', async ({ page }) => {
    await page.goto(`${BASE}/flash-sales`);
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toBeVisible();
  });

  test('coupons page loads', async ({ page }) => {
    await page.goto(`${BASE}/coupons`);
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toBeVisible();
  });

  test('profile page loads', async ({ page }) => {
    await page.goto(`${BASE}/profile`);
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toBeVisible();
  });

  test('settings page loads', async ({ page }) => {
    await page.goto(`${BASE}/settings`);
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toBeVisible();
  });
});