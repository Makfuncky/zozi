const { chromium } = require('@playwright/test');
const BASE = 'http://localhost:3000';

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const crashes = [];
  page.on('pageerror', (err) => {
    crashes.push(`[${page.url().split('?')[1]||''}] PAGEERR ${err.message}`);
  });

  await page.goto(`${BASE}/admin/login`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.fill('input[placeholder="Your username"]', 'admin');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/admin/dashboard', { timeout: 15000 });
  await page.waitForTimeout(1500);

  const VALID = ['finance','payouts','bank-accounts','treasury','chart-of-accounts','expense-scan','bank-mapping','fixed-assets','accruals','ar','ap','journal','payments','reconciliation','budgets','audit','fx','deferred-revenue','email-ledger','ai-reconcile','trial-balance','pl','balance-sheet','cash-flow','periods','reversal','forecast','reports'];
  for (const t of VALID) {
    try {
      await page.goto(`${BASE}/admin/finance?section=${t}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    } catch (e) {
      crashes.push(`[${t}] GOTO TIMEOUT ${e.message.split('\n')[0]}`);
      continue;
    }
    await page.waitForTimeout(3000);
    const err = await page.evaluate(() => {
      const t = document.body.innerText;
      const m = t.match(/crashed[: ]+(.+?)(Retry|$)/i);
      return m ? m[1].trim() : null;
    });
    if (err) crashes.push(`[${t}] CRASH: ${err}`);
    else console.log(`OK ${t.padEnd(18)} chars=${ (await page.evaluate(()=>document.body.innerText.length)) }`);
  }
  await browser.close();
  console.log('\n=== CRASHES (' + crashes.length + ') ===');
  console.log(crashes.length ? crashes.join('\n') : 'NONE');
})();
