# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: mobile-smoke.spec.ts >> Mobile App Smoke Tests >> Wishlist tab is visible after parity fix F-7
- Location: e2e\mobile-smoke.spec.ts:15:7

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
  6  |     await page.waitForTimeout(2000);
  7  |   });
  8  | 
  9  |   test('home screen renders with header and navigation', async ({ page }) => {
  10 |     await expect(page.getByRole('tab', { name: /Shop/i })).toBeVisible();
  11 |     await expect(page.getByRole('tab', { name: /Cart/i })).toBeVisible();
  12 |     await expect(page.getByRole('tab', { name: /Sign In/i })).toBeVisible();
  13 |   });
  14 | 
  15 |   test('Wishlist tab is visible after parity fix F-7', async ({ page }) => {
  16 |     await expect(page.getByRole('tab', { name: /Wishlist/i })).toBeVisible();
  17 |   });
  18 | 
  19 |   test('Orders tab is visible after parity fix F-7', async ({ page }) => {
  20 |     await expect(page.getByRole('tab', { name: /Orders/i })).toBeVisible();
  21 |   });
  22 | 
  23 |   test('Shop tab is visible and clickable', async ({ page }) => {
  24 |     const shopTab = page.getByRole('tab', { name: /Shop/i });
  25 |     await expect(shopTab).toBeVisible();
  26 |     await shopTab.click();
  27 |     await page.waitForURL(/\/products/);
  28 |   });
  29 | 
  30 |   test('Cart tab is visible and clickable', async ({ page }) => {
  31 |     const cartTab = page.getByRole('tab', { name: /Cart/i });
  32 |     await expect(cartTab).toBeVisible();
  33 |     await cartTab.click();
  34 |     await page.waitForURL(/\/cart/);
  35 |   });
  36 | 
  37 |   test('Account/Sign In tab is visible and clickable', async ({ page }) => {
  38 |     const accountTab = page.getByRole('tab', { name: /Sign In/i });
  39 |     await expect(accountTab).toBeVisible();
  40 |     await accountTab.click();
  41 |     await page.waitForURL(/\/(profile|login)/);
  42 |   });
  43 | 
  44 |   test('bottom tab bar has exactly 5 tabs (Shop/Wishlist/Orders/Cart/Account)', async ({ page }) => {
  45 |     const tabs = page.locator('[role="tab"]');
  46 |     const count = await tabs.count();
  47 |     expect(count).toBe(5);
  48 |   });
  49 | 
  50 |   test('no console errors on initial load', async ({ page }) => {
  51 |     const errors = [];
  52 |     page.on('console', (msg) => {
  53 |       if (msg.type() === 'error') errors.push(msg.text());
  54 |     });
  55 |     await page.goto('/', { waitUntil: 'networkidle' });
  56 |     await page.waitForTimeout(2000);
  57 |     const authErrors = errors.filter((e) => !e.includes('401') && !e.includes('404'));
  58 |     expect(authErrors).toEqual([]);
  59 |   });
  60 | 
  61 |   test('no page errors on initial load', async ({ page }) => {
  62 |     const errors = [];
  63 |     page.on('pageerror', (err) => errors.push(err.message));
  64 |     await page.goto('/', { waitUntil: 'networkidle' });
  65 |     await page.waitForTimeout(2000);
  66 |     expect(errors).toEqual([]);
  67 |   });
  68 | });
```