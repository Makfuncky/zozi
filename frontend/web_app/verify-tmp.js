const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const results = {};

  async function measure(locale, file) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 1000 } });
    const page = await ctx.newPage();
    await page.addInitScript((key, val) => {
      try { localStorage.setItem(key, val); } catch (e) {}
    }, 'zozi_locale', locale);
    const errors = [], failed = [];
    const jsErrors = [];
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', e => { jsErrors.push(e.message + (e.stack ? '\n' + e.stack.split('\n').slice(0,3).join('\n') : '')); });
    page.on('response', r => { if (r.status() >= 400) failed.push(r.status() + ' ' + r.url()); });
    await page.goto('http://localhost:3000/products/1', { waitUntil: 'load', timeout: 120000 });
    await page.waitForTimeout(8000);

    await page.screenshot({ path: file, fullPage: true });

    const data = await page.evaluate(() => {
      const vw = window.innerWidth;
      const dir = document.documentElement.dir;
      const bodyText = document.body.innerText.replace(/\s+/g, ' ').slice(0, 600);
      // gather headings
      const headings = [...document.querySelectorAll('h1,h2,h3')].map(h => h.textContent.trim()).filter(Boolean).slice(0, 20);
      function findCard(headingText) {
        const heads = [...document.querySelectorAll('h1,h2,h3')];
        let heading = heads.find(h => (h.textContent||'').trim().toLowerCase().includes(headingText.toLowerCase()));
        if (!heading) return null;
        let el = heading;
        for (let i = 0; i < 6; i++) {
          el = el.parentElement;
          if (!el) break;
          const cs = getComputedStyle(el);
          if (parseFloat(cs.paddingTop) > 0 || cs.borderTopWidth !== '0px' || cs.backgroundColor !== 'rgba(0, 0, 0, 0)') {
            const r = el.getBoundingClientRect();
            return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), right: Math.round(r.right), ml: Math.round(r.x), mr: Math.round(vw - r.right) };
          }
        }
        const r = heading.getBoundingClientRect();
        return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), right: Math.round(r.right) };
      }
      return {
        dir, vw, bodyText, headings,
        description: findCard('Supplier Product Description'),
        reviews: findCard('Reviews'),
        recommendations: findCard('You May Also Like'),
      };
    });
    results[locale] = { errors, jsErrors, failed, ...data };
    await ctx.close();
  }

  await measure('en', 'C:/Users/user/AppData/Local/Temp/kilo/prod-en.png');
  await measure('ar', 'C:/Users/user/AppData/Local/Temp/kilo/prod-ar.png');

  console.log(JSON.stringify(results, null, 2));
  await browser.close();
})();
