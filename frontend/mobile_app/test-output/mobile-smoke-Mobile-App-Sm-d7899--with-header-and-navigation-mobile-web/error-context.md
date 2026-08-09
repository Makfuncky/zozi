# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: mobile-smoke.spec.ts >> Mobile App Smoke Tests >> home screen renders with header and navigation
- Location: e2e\mobile-smoke.spec.ts:8:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:8090/
Call log:
  - navigating to "http://localhost:8090/", waiting until "networkidle"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Mobile App Smoke Tests', () => {
  4  |   test.beforeEach(async ({ page }) => {
> 5  |     await page.goto('/', { waitUntil: 'networkidle' });
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:8090/
  6  |   });
  7  | 
  8  |   test('home screen renders with header and navigation', async ({ page }) => {
  9  |     await expect(page.locator('body')).toBeVisible();
  10 |     const bodyText = await page.textContent('body');
  11 |     expect(bodyText).toContain('ZOZI');
  12 |   });
  13 | 
  14 |   test('Shop tab is visible and clickable', async ({ page }) => {
  15 |     const shopTab = page.getByRole('button', { name: /Shop/i });
  16 |     await expect(shopTab).toBeVisible();
  17 |     await shopTab.click();
  18 |     await page.waitForTimeout(1000);
  19 |     const url = page.url();
  20 |     expect(url).toContain('/products');
  21 |   });
  22 | 
  23 |   test('Cart tab is visible and clickable', async ({ page }) => {
  24 |     const cartTab = page.getByRole('button', { name: /Cart/i });
  25 |     await expect(cartTab).toBeVisible();
  26 |     await cartTab.click();
  27 |     await page.waitForTimeout(1000);
  28 |     const url = page.url();
  29 |     expect(url).toContain('/cart');
  30 |   });
  31 | 
  32 |   test('Account/Sign In tab is visible and clickable', async ({ page }) => {
  33 |     const accountTab = page.getByRole('button', { name: /Account|Sign In/i });
  34 |     await expect(accountTab).toBeVisible();
  35 |     await accountTab.click();
  36 |     await page.waitForTimeout(1000);
  37 |     const url = page.url();
  38 |     expect(url).toMatch(/\/(profile|login)/);
  39 |   });
  40 | 
  41 |   test('bottom tab bar has exactly 3 tabs', async ({ page }) => {
  42 |     const tabs = page.locator('[role="tab"]');
  43 |     const count = await tabs.count();
  44 |     expect(count).toBeGreaterThanOrEqual(2);
  45 |   });
  46 | 
  47 |   test('drawer menu opens from left', async ({ page }) => {
  48 |     const menuBtn = page.getByRole('button', { name: /Open menu/i });
  49 |     await expect(menuBtn).toBeVisible();
  50 |     await menuBtn.click();
  51 |     await page.waitForTimeout(500);
  52 |     const drawer = page.locator('text=Shop').first();
  53 |     await expect(drawer).toBeVisible();
  54 |   });
  55 | 
  56 |   test('all drawer menu items are accessible', async ({ page }) => {
  57 |     const menuBtn = page.getByRole('button', { name: /Open menu/i });
  58 |     await menuBtn.click();
  59 |     await page.waitForTimeout(500);
  60 | 
  61 |     const menuItems = ['Shop', 'Wishlist', 'Offers', 'Flash Sales', 'Help Center'];
  62 |     for (const item of menuItems) {
  63 |       const link = page.getByRole('link', { name: item }).or(page.getByRole('button', { name: item }));
  64 |       await expect(link.first()).toBeVisible();
  65 |     }
  66 |   });
  67 | 
  68 |   test('no console errors on initial load', async ({ page }) => {
  69 |     const errors: string[] = [];
  70 |     page.on('console', (msg) => {
  71 |       if (msg.type() === 'error') errors.push(msg.text());
  72 |     });
  73 |     await page.goto('/', { waitUntil: 'networkidle' });
  74 |     const authErrors = errors.filter((e) => !e.includes('401') && !e.includes('404'));
  75 |     expect(authErrors).toEqual([]);
  76 |   });
  77 | 
  78 |   test('no page errors on initial load', async ({ page }) => {
  79 |     const errors: string[] = [];
  80 |     page.on('pageerror', (err) => errors.push(err.message));
  81 |     await page.goto('/', { waitUntil: 'networkidle' });
  82 |     expect(errors).toEqual([]);
  83 |   });
  84 | });
```