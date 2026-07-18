const { chromium } = require('@playwright/test');
const BASE = 'http://localhost:3000';
const TABS = ['fx','deferred-revenue','email-ledger','ai-reconcile','budgets','accruals'];
const markers = {
  fx: ['Save Rate','Run Revaluation','Base','Quote'],
  'deferred-revenue': ['Create Contract','Run Amortization','Recognized'],
  'email-ledger': ['Parse & Draft','billing@acme.com'],
  'ai-reconcile': ['Run AI Reconcile','Bank import ID'],
  budgets: ['No budget data','Fiscal Period'],
  accruals: ['Post Accrual','No accruals'],
};
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
    const full = await page.evaluate(() => document.body.innerText);
    const found = markers[t].filter(m => full.includes(m));
    console.log(`${t}: markers found [${found.join(', ')}] / ${markers[t].length}`);
  }
  await browser.close();
})();
