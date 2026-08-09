const { chromium } = require('@playwright/test');
const BASE = 'http://localhost:3000';

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto(`${BASE}/admin/login`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.fill('input[placeholder="Your username"]', 'admin');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/admin/dashboard', { timeout: 15000 });
  await page.waitForTimeout(2000);

  for (const t of ['overview','ar','ap','gl','journal','treasury','expenses','budgets']) {
    await page.goto(`${BASE}/admin/finance?section=${t}`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3500);
    const info = await page.evaluate(() => {
      const txt = document.body.innerText;
      const tables = document.querySelectorAll('table').length;
      const buttons = document.querySelectorAll('button').length;
      const inputs = document.querySelectorAll('input,select,textarea').length;
      // find "loading" or empty states
      const loading = /loading|fetching|please wait/i.test(txt.slice(0,500));
      return { len: txt.length, tables, buttons, inputs, snippet: txt.replace(/\s+/g,' ').slice(0,180) };
    });
    console.log(`TAB ${t.padEnd(10)} chars=${info.len} tables=${info.tables} btns=${info.buttons} inputs=${info.inputs}`);
    console.log(`   "${info.snippet}"`);
  }
  await browser.close();
})();
