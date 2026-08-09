const { chromium } = require('@playwright/test');

const BASE = 'http://localhost:3000';
const TABS = [
  'overview','dashboard','gl','journal','subledger','ar','ap','accruals',
  'expenses','budgets','fx','deferred','assets','reconcile','treasury',
  'cashflow','fxrates','payments','tax','reports','payroll','costing',
  'settings','forecast','audit','closure','interco','manual'
];

const errors = [];
const consoleErrors = [];

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(`[${page.url()}] ${msg.text()}`);
  });
  page.on('pageerror', (err) => {
    errors.push(`[${page.url()}] ${err.message}`);
  });

  for (const t of TABS) {
    const url = `${BASE}/admin/finance?section=${t}`;
    try {
      const resp = await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
      const status = resp ? resp.status() : 'n/a';
      const title = await page.title();
      console.log(`TAB ${t.padEnd(10)} status=${status} title="${title}"`);
    } catch (e) {
      console.log(`TAB ${t.padEnd(10)} ERROR ${e.message}`);
    }
  }

  await browser.close();

  console.log('\n=== PAGE ERRORS ===');
  console.log(errors.length ? errors.join('\n') : 'none');
  console.log('\n=== CONSOLE ERRORS ===');
  console.log(consoleErrors.length ? consoleErrors.join('\n') : 'none');
})();
