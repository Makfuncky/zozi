const { chromium } = require('playwright');
const BASE = 'http://localhost:3000';
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0,200)); });
  page.on('pageerror', e => errors.push('PAGEERR: ' + e.message.slice(0,200)));
  try {
    const resp = await page.goto(BASE + '/cart', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2500);
    console.log('status', resp && resp.status());
    console.log('url', page.url());
    console.log('body', (await page.evaluate(() => document.body.innerText.replace(/\n/g,' '))).slice(0,300));
  } catch (e) {
    console.log('GOTO ERR', e.message.split('\n')[0]);
    console.log('url', page.url());
  }
  console.log('CONSOLE ERRORS:');
  errors.slice(0,15).forEach(e => console.log(' -', e));
  await browser.close();
})();
