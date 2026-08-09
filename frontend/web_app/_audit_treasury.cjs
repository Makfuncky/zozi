const { chromium } = require('@playwright/test');
const BASE = 'http://localhost:3000';
(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const crashes = [];
  page.on('pageerror', e => crashes.push('PAGEERR ' + e.message));
  await page.goto(`${BASE}/admin/login`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.fill('input[placeholder="Your username"]', 'admin');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/admin/dashboard', { timeout: 15000 });
  await page.waitForTimeout(1500);

  // Global view (consolidated) - this was the crash trigger
  await page.goto(`${BASE}/admin/finance?section=treasury`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(5000);
  const globalTxt = await page.evaluate(() => document.body.innerText);
  const globalCrash = /crashed[: ]+(.+?)(Retry|$)/i.test(globalTxt);
  const hasDash = globalTxt.includes('Treasury') || globalTxt.includes('Cash Position');
  console.log('GLOBAL VIEW treasury: crash=' + globalCrash + ' hasContent=' + hasDash);
  console.log('markers:', ['Dashboard','Cash Position','Total Cash','Free Cash'].filter(m=>globalTxt.includes(m)).join(', '));

  // Now switch to a specific country via the filter if present
  await browser.close();
  console.log('CRASHES:', crashes.length ? crashes.join('\n') : 'NONE');
})();
