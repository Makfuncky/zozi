const { chromium } = require('@playwright/test');
const BASE = 'http://localhost:3000';
const TABS = ['accruals','ar','ap','journal','reconciliation','budgets','audit','fx','deferred-revenue','email-ledger','ai-reconcile','trial-balance','balance-sheet'];

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
    // main content is the last PanelContent; grab text after "Reports" nav entry
    const info = await page.evaluate(() => {
      const main = document.querySelector('main') || document.body;
      const txt = main.innerText;
      // find index after the tab-nav "Reports" marker
      const idx = txt.lastIndexOf('Reports');
      const after = idx >= 0 ? txt.slice(idx + 50) : txt;
      const headings = Array.from(document.querySelectorAll('h1,h2,h3')).map(h=>h.innerText).filter(Boolean);
      return { afterLen: after.length, headings: headings.slice(0,4), afterSnippet: after.replace(/\s+/g,' ').slice(0,200) };
    });
    console.log(`\n### ${t}  (contentLen=${info.afterLen})`);
    console.log('  headings:', info.headings.join(' | '));
    console.log('  text:', info.afterSnippet);
  }
  await browser.close();
})();
