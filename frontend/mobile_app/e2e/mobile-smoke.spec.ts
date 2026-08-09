import { test, expect } from '@playwright/test';

test.describe('Mobile App Smoke Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
  });

  test('home screen renders with header and navigation', async ({ page }) => {
    await expect(page.getByRole('tab', { name: /Shop/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Cart/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Sign In/i })).toBeVisible();
  });

  test('Shop tab is visible and clickable', async ({ page }) => {
    const shopTab = page.getByRole('tab', { name: /Shop/i });
    await expect(shopTab).toBeVisible();
    await shopTab.click();
    await page.waitForURL(/\/products/);
  });

  test('Cart tab is visible and clickable', async ({ page }) => {
    const cartTab = page.getByRole('tab', { name: /Cart/i });
    await expect(cartTab).toBeVisible();
    await cartTab.click();
    await page.waitForURL(/\/cart/);
  });

  test('Account/Sign In tab is visible and clickable', async ({ page }) => {
    const accountTab = page.getByRole('tab', { name: /Sign In/i });
    await expect(accountTab).toBeVisible();
    await accountTab.click();
    await page.waitForURL(/\/(profile|login)/);
  });

  test('bottom tab bar has exactly 3 tabs', async ({ page }) => {
    const tabs = page.locator('[role="tab"]');
    const count = await tabs.count();
    expect(count).toBe(3);
  });

  test('no console errors on initial load', async ({ page }) => {
    const errors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    const authErrors = errors.filter((e) => !e.includes('401') && !e.includes('404'));
    expect(authErrors).toEqual([]);
  });

  test('no page errors on initial load', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(err.message));
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    expect(errors).toEqual([]);
  });
});