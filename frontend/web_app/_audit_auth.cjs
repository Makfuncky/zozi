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
    if (msg.type() === 'error') consoleErrors.push(`[${page.url().split('?')[1]||''}] ${msg.text()}`);
  });
  page.on('pageerror', (err) => {
    errors.push(`[${page.url().split('?')[1]||''}] ${err.message}`);
  });

  // Real login
  await page.goto(`${BASE}/admin/login`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.fill('input[placeholder="Your username"]', 'admin');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/admin/**', { timeout: 15000 }).catch(()=>{});
  await page.waitForTimeout(2500);
  console.log('After login URL:', page.url());

  for (const t of TABS) {
    const url = `${BASE}/admin/finance?section=${t}`;
    try {
      const resp = await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
      const status = resp ? resp.status() : 'n/a';
      const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 150));
      const hasError = /something went wrong|error boundary|undefined is not|cannot read|application error/i.test(bodyText);
      // check that we're actually on finance, not redirected to login
      const onLogin = page.url().includes('/admin/login');
      console.log(`TAB ${t.padEnd(10)} status=${status} login=${onLogin} errText=${hasError}`);
    } catch (e) {
      console.log(`TAB ${t.padEnd(10)} ERROR ${e.message}`);
    }
  }

  await browser.close();

  const ce = [...new Set(consoleErrors)];
  console.log('\n=== PAGE ERRORS (' + errors.length + ') ===');
  console.log(errors.length ? [...new Set(errors)].join('\n') : 'none');
  console.log('\n=== CONSOLE ERRORS (' + ce.length + ' unique) ===');
  console.log(ce.length ? ce.join('\n') : 'none');
})();
