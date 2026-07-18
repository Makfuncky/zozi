const { chromium } = require('@playwright/test');

const BASE = 'http://localhost:3000';
const TABS = ['overview','deferred','payments','payroll','interco'];

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();

  const failed = [];
  page.on('requestfailed', (req) => {
    failed.push(`[${page.url().split('?')[1]}] REQFAIL ${req.url()} :: ${req.failure()?.errorText}`);
  });
  page.on('response', (resp) => {
    const u = resp.url();
    if ((u.includes('countries') || u.includes('api/geo') || u.includes('currency/context')) && resp.status() >= 400) {
      failed.push(`[${page.url().split('?')[1]}] HTTP ${resp.status()} ${u}`);
    }
  });

  for (const t of TABS) {
    const url = `${BASE}/admin/finance?section=${t}`;
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    // allow fetches to fire + settle
    await page.waitForTimeout(4000);
  }

  await browser.close();
  console.log(failed.length ? failed.join('\n') : 'NO FAILED COUNTRY/GEO/CURRENCY REQUESTS');
})();
