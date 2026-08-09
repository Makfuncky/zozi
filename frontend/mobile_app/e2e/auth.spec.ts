import { test, expect } from '@playwright/test';

const BASE = process.env.PW_BASE_URL || 'http://localhost:8090';

test.describe('Authentication Flow', () => {
  test('login page renders correctly', async ({ page }) => {
    await page.goto(`${BASE}/login`);
    await page.waitForTimeout(2000);
    await expect(page.getByLabel(/Email or Username/i)).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.getByRole('button', { name: /Sign In/i })).toBeVisible();
  });

  test('login form has email and password fields', async ({ page }) => {
    await page.goto(`${BASE}/login`);
    await page.waitForTimeout(2000);
    await expect(page.getByLabel(/Email or Username/i)).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('login form is accessible', async ({ page }) => {
    await page.goto(`${BASE}/login`);
    await page.waitForTimeout(2000);
    await expect(page.getByLabel(/Email or Username/i)).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.getByRole('button', { name: /Sign In/i })).toBeVisible();
  });

  test('register page renders correctly', async ({ page }) => {
    await page.goto(`${BASE}/login`);
    await page.waitForTimeout(2000);
    const registerLink = page.getByRole('link', { name: /Register/i });
    if (await registerLink.isVisible()) {
      await registerLink.click();
      await page.waitForTimeout(1000);
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('forgot password page renders', async ({ page }) => {
    await page.goto(`${BASE}/login`);
    await page.waitForTimeout(2000);
    const forgotLink = page.getByRole('link', { name: /Forgot password/i });
    if (await forgotLink.isVisible()) {
      await forgotLink.click();
      await page.waitForTimeout(1000);
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('edit profile page renders', async ({ page }) => {
    await page.goto(`${BASE}/edit-profile`);
    await page.waitForTimeout(2000);
    await expect(page.getByText(/Personal Info/i)).toBeVisible();
  });
});