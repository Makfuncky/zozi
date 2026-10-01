// Self-contained: serve web-dist, run Playwright smoke, then exit.
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '..', 'web-dist');
const PORT = process.env.PW_PORT || 8090;
const OUT_DIR = path.resolve(__dirname, '..', 'playwright-out');
const BASE = `http://localhost:${PORT}/`;

const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.ico': 'image/x-icon',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.ttf': 'font/ttf',
  '.woff': 'font/woff', '.woff2': 'font/woff2', '.map': 'application/json',
};

const server = http.createServer((req, res) => {
  let urlPath = decodeURIComponent(req.url.split('?')[0]);
  if (urlPath === '/') urlPath = '/index.html';
  let filePath = path.join(ROOT, urlPath);
  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    filePath = path.join(ROOT, 'index.html');
  }
  fs.readFile(filePath, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not found'); return; }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  });
});

const TABS = ['Shop', 'Cart', 'Sign In'];
const ROUTES = [
  '/login', '/edit-profile', '/orders', '/wishlist', '/notifications', '/offers',
  '/products', '/products/1', '/cart', '/checkout', '/flash-sales', '/coupons',
  '/profile', '/settings', '/returns',
];

server.listen(PORT, async () => {
  console.log('Serving on ' + PORT);
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    userAgent: 'Mozilla/5.0 (Playwright-Smoke) ZOZI',
  });
  const page = await context.newPage();
  const consoleErrors = [], pageErrors = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', (e) => pageErrors.push(e.message));

  try { await page.goto(BASE, { waitUntil: 'load', timeout: 60000 }); }
  catch (e) { console.error('Navigation failed:', e.message); }

  let mounted = false;
  try { await page.waitForSelector('#root > *', { timeout: 30000 }); mounted = true; }
  catch (e) { console.error('App root did not mount:', e.message); }
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(OUT_DIR, '00-home.png') });

  const bodyText = (await page.evaluate(() => document.body.innerText)).slice(0, 500).replace(/\n+/g, ' | ');
  console.log('Body text:', bodyText);

  for (let i = 0; i < TABS.length; i++) {
    const label = TABS[i];
    try {
      const clicked = await page.evaluate((tab) => {
        const els = Array.from(document.querySelectorAll('button, a, [role="button"]'));
        const norm = (s) => (s || '').replace(/[^a-z0-9]/gi, '').toLowerCase();
        const el = els.find((e) => norm(e.innerText).includes(norm(tab)));
        if (el) { el.click(); return true; }
        return false;
      }, label);
      if (clicked) {
        await page.waitForTimeout(2000);
        await page.screenshot({ path: path.join(OUT_DIR, `0${i + 1}-${label}.png`) });
        console.log('Clicked tab:', label);
      } else console.log('Tab not found:', label);
    } catch (e) { console.error(`Tab ${label} error:`, e.message); }
  }

  // Visit deep routes directly to surface runtime errors on each screen.
  for (let i = 0; i < ROUTES.length; i++) {
    const route = ROUTES[i];
    try {
      await page.goto(BASE + route.replace(/^\//, '') + '?skip', { waitUntil: 'load', timeout: 30000 });
      await page.waitForTimeout(2000);
      await page.screenshot({ path: path.join(OUT_DIR, `route-${i}-${route.replace(/\//g, '_')}.png`) });
      const txt = (await page.evaluate(() => document.body.innerText)).replace(/\s+/g, ' ').trim().slice(0, 200);
      const empty = txt.length < 5;
      console.log(`Visited ${route} | empty=${empty} | "${txt}"`);
    } catch (e) { console.error(`Route ${route} error:`, e.message); }
  }

  console.log('\n=== CONSOLE ERRORS (' + consoleErrors.length + ') ===');
  consoleErrors.slice(0, 30).forEach((e) => console.log(' -', e.slice(0, 300)));
  console.log('\n=== PAGE ERRORS (' + pageErrors.length + ') ===');
  pageErrors.slice(0, 30).forEach((e) => console.log(' -', e.slice(0, 300)));

  const summary = { mounted, consoleErrors: consoleErrors.slice(0, 30), pageErrors: pageErrors.slice(0, 30), bodyText };
  fs.writeFileSync(path.join(OUT_DIR, 'summary.json'), JSON.stringify(summary, null, 2));
  await browser.close();
  server.close();
  process.exit(0);
});
