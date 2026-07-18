const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:3000/products/3-silk-scarf', { waitUntil: 'domcontentloaded', timeout: 40000 });
  await page.waitForTimeout(3500);
  const imgs = await page.evaluate(() =>
    Array.from(document.images).map(i => ({
      h: Math.round(i.getBoundingClientRect().height),
      w: Math.round(i.getBoundingClientRect().width),
      parent: i.parentElement ? i.parentElement.className.slice(0,40) : '',
      src: (i.currentSrc || i.src || '').split('/').pop().slice(0,30),
    })).filter(im => im.h === 0)
  );
  console.log('ZERO-HEIGHT COUNT', imgs.length);
  imgs.forEach((im, idx) => console.log(idx, 'w='+im.w, im.parent, im.src));
  await browser.close();
})();
