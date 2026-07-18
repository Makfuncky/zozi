const { chromium } = require('@playwright/test');

const BASE = 'http://localhost:3000';

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();

  const results = [];
  page.on('response', (resp) => {
    const u = resp.url();
    if (u.includes('/api/geo') || u.includes('/__api/countries') || u.includes('/auth/me') || u.includes('/auth/refresh') || u.includes('/api/currency/context')) {
      results.push(`${resp.status()} ${u}`);
    }
  });
  page.on('requestfailed', (req) => {
    const u = req.url();
    if (u.includes('/api/geo') || u.includes('/__api/countries') || u.includes('/auth/me') || u.includes('/auth/refresh')) {
      results.push(`FAIL ${u} :: ${req.failure()?.errorText}`);
    }
  });

  await page.goto(`${BASE}/admin/login`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.fill('input[placeholder="Your username"]', 'admin');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/admin/dashboard', { timeout: 15000 });
  // give providers time to settle
  await page.waitForTimeout(6000);

  // navigate to one finance tab and wait
  await page.goto(`${BASE}/admin/finance?section=overview`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(6000);

  await browser.close();
  console.log([...new Set(results)].join('\n'));
})();
