const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('console', m => { if (m.type()==='error') errors.push(m.text().slice(0,300)); });
  page.on('pageerror', e => errors.push('PAGEERR ' + e.message.slice(0,300)));
  await page.goto('http://localhost:3000/products/3-silk-scarf', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);
  const info = await page.evaluate(() => {
    const img = document.querySelector('img[src*="scarf1"]');
    if (!img) return { found: false };
    const parent = img.parentElement;
    const cs = getComputedStyle(parent);
    return { found: true, parentClass: parent.className.slice(0,200), height: cs.height, minHeight: cs.minHeight, aspectRatio: cs.aspectRatio, position: cs.position };
  });
  console.log(JSON.stringify(info, null, 2));
  console.log('ERRORS:', errors.slice(0,10));
  await browser.close();
})();
