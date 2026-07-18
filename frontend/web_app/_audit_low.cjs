const { chromium } = require('@playwright/test');
const BASE = 'http://localhost:3000';
const lowTabs = ['accruals','ar','ap','journal','reconciliation','budgets','audit','fx','deferred-revenue','email-ledger','ai-reconcile','trial-balance','balance-sheet'];

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
  for (const t of lowTabs) {
    await page.goto(`${BASE}/admin/finance?section=${t}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3000);
    const txt = await page.evaluate(() => document.body.innerText.replace(/\s+/g,' ').slice(0,300));
    console.log(`\n### ${t}\n${txt}`);
  }
  await browser.close();
})();
