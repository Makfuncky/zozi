const { chromium } = require('@playwright/test');
const BASE = 'http://localhost:3000';
(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto(`${BASE}/admin/login`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.fill('input[placeholder="Your username"]', 'admin');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/admin/dashboard', { timeout: 15000 });
  await page.waitForTimeout(1500);
  await page.goto(`${BASE}/admin/finance?section=ar`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(4000);
  const len = await page.evaluate(() => document.body.innerText.length);
  // get text AFTER the sidebar nav (skip first 600 chars which is nav)
  const full = await page.evaluate(() => document.body.innerText);
  console.log('TOTAL LEN:', len);
  console.log('AFTER NAV (chars 600+):');
  console.log(full.slice(600, 1200));
  await browser.close();
})();
