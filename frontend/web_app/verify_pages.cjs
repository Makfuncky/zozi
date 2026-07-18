const { chromium } = require('playwright');

const BASE = process.env.BASE || 'http://localhost:3000';
const PAGES = [
  '/',
  '/products/3-silk-scarf',
  '/suppliers/2',
  '/cart',
  '/checkout',
  '/supplier/register',
];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const path of PAGES) {
    const url = BASE + path;
    try {
      const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForTimeout(2500);
      const status = resp ? resp.status() : 'n/a';
      const title = await page.title();
      // basic 404 detection
      const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 200));
      const hasNotFound = /404|Page Not Found|not found/i.test(title + ' ' + bodyText);
      // count images with height 0
      const zeroImgs = await page.evaluate(() =>
        Array.from(document.images).filter(i => i.getBoundingClientRect().height === 0).length
      );
      console.log(`[${status}] ${path} | title="${title}" | 404=${hasNotFound} | zeroHeightImgs=${zeroImgs} | body="${bodyText.replace(/\n/g,' ').slice(0,80)}"`);
    } catch (e) {
      console.log(`[ERR] ${path} | ${e.message.split('\n')[0]}`);
    }
  }
  await browser.close();
})();
