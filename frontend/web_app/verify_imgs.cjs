const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:3000/products/3-silk-scarf', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);
  const imgs = await page.evaluate(() =>
    Array.from(document.images).map(i => ({
      h: Math.round(i.getBoundingClientRect().height),
      w: Math.round(i.getBoundingClientRect().width),
      src: i.currentSrc || i.src || '',
    }))
  );
  console.log('IMG COUNT', imgs.length);
  imgs.forEach((im, idx) => console.log(idx, 'h=' + im.h, 'w=' + im.w, im.src.slice(0, 80)));
  await browser.close();
})();
