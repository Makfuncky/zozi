// Standalone Playwright smoke test for the ZOZI Expo web build.
// Loads the app, walks the bottom tab bar, captures console/page errors and screenshots.
const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PW_PORT || 8081;
const BASE = `http://localhost:${PORT}/`;
const OUT_DIR = path.resolve(process.cwd(), 'playwright-out');

const TABS = ['Shop', 'Cart', 'Account', 'Sign In'];

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    userAgent: 'Mozilla/5.0 (Playwright-Smoke) ZOZI',
  });
  const page = await context.newPage();

  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => pageErrors.push(err.message));

  console.log(`\n=== Navigating to ${BASE} ===`);
  try {
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 90000 });
  } catch (e) {
    console.error('Navigation failed:', e.message);
  }

  let mounted = false;
  try {
    await page.waitForSelector('body > div', { timeout: 30000 });
    mounted = true;
  } catch (e) {
    console.error('App root did not mount:', e.message);
  }
  await page.screenshot({ path: path.join(OUT_DIR, '00-home.png'), fullPage: false });

  const bodyText = (await page.evaluate(() => document.body.innerText)).slice(0, 500).replace(/\n+/g, ' | ');
  console.log('Body text (first 500):', bodyText);

  for (let i = 0; i < TABS.length; i++) {
    const label = TABS[i];
    try {
      const clicked = await page.evaluate((tab) => {
        const els = Array.from(document.querySelectorAll('button, a, [role="button"]'));
        const el = els.find((e) => (e.innerText || '').trim().toLowerCase().startsWith(tab.toLowerCase()));
        if (el) { el.click(); return true; }
        return false;
      }, label);
      if (clicked) {
        await page.waitForTimeout(1500);
        await page.screenshot({ path: path.join(OUT_DIR, `0${i + 1}-${label}.png`), fullPage: false });
        console.log(`Clicked tab: ${label}`);
      } else {
        console.log(`Tab not found (clickable): ${label}`);
      }
    } catch (e) {
      console.error(`Error interacting with tab ${label}:`, e.message);
    }
  }

  console.log('\n=== CONSOLE ERRORS (' + consoleErrors.length + ') ===');
  consoleErrors.slice(0, 50).forEach((e) => console.log(' -', e));
  console.log('\n=== PAGE ERRORS (' + pageErrors.length + ') ===');
  pageErrors.slice(0, 50).forEach((e) => console.log(' -', e));

  await browser.close();

  const summary = { mounted, consoleErrors, pageErrors, bodyText };
  fs.writeFileSync(path.join(OUT_DIR, 'summary.json'), JSON.stringify(summary, null, 2));
  console.log('\nDone. Output in', OUT_DIR);
}

main().catch((e) => {
  console.error('Fatal:', e);
  process.exit(1);
});
