const { chromium } = require('@playwright/test');
const BASE = 'http://localhost:3000';
const TABS = ['fx','deferred-revenue','email-ledger','ai-reconcile'];
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
  for (const t of TABS) {
    await page.goto(`${BASE}/admin/finance?section=${t}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(4000);
    const html = await page.evaluate(() => {
      const main = document.querySelector('main');
      return main ? main.innerHTML.slice(0, 600) : 'NO MAIN';
    });
    console.log(`\n### ${t}\nMAIN HTML (first 600):\n${html}`);
  }
  await browser.close();
})();
