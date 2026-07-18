const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const b64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
const pngPath = path.join(process.env.TEMP || 'C:\\Temp', 'zozi_test_product.png');
fs.writeFileSync(pngPath, Buffer.from(b64, 'base64'));

const log = (...a) => { console.log(...a); };
const flush = () => new Promise(r => setTimeout(r, 0));
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error' && !/WebSocket|ws:\/\//.test(m.text())) errors.push('CONSOLE: ' + m.text()); });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));

  const base = 'http://127.0.0.1:3000';
  const go = async (url) => { await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }); await sleep(1500); };

  // Resilient login (dev server can be slow / HMR-flaky)
  let loggedIn = false;
  for (let attempt = 1; attempt <= 3 && !loggedIn; attempt++) {
    await go(base + '/supplier/login');
    await page.fill('input[placeholder="Username"]', 'supplier@zozi.com').catch(e => log('user miss', e.message));
    await page.fill('input[type="password"]', 'supplier123').catch(e => log('pw miss', e.message));
    await page.click('button:has-text("Sign In")').catch(e => log('signin click miss', e.message));
    try { await page.waitForURL('**/supplier/dashboard', { timeout: 30000, waitUntil: 'domcontentloaded' }); loggedIn = true; } catch (e) { log('login attempt', attempt, 'redirect timeout', e.message); }
    await sleep(1500);
  }
  log('After login URL:', page.url());
  await flush();

  if (!page.url().includes('/supplier/dashboard')) {
    log('LOGIN DID NOT REDIRECT — dumping page text for clues');
    const bodyTxt = await page.locator('body').innerText().catch(() => '(no body)');
    log(bodyTxt.slice(0, 500));
  }
  await flush();

  await go(base + '/supplier/products/add');
  await sleep(1000);

  // Upload: the first file input is the "Choose Photo" image input (hidden,
  // but Playwright can set files on it directly). Do NOT click the label first.
  const fileInput = page.locator('input[type="file"]').first();
  const hasInput = await fileInput.count();
  log('file input count:', hasInput);
  if (hasInput) {
    await fileInput.setInputFiles(pngPath);
    log('File uploaded. Waiting for AI analysis + auto matrix...');
    await sleep(16000);
  }
  await flush();

  const nameVal = await page.locator('input[placeholder*="auto-detect" i]').first().inputValue().catch(() => '(none)');
  log('Product name after AI:', JSON.stringify(nameVal));
  const categoryVal = await page.locator('select').first().inputValue().catch(() => '(none)');
  log('Category after AI:', JSON.stringify(categoryVal));
  await flush();

  const matrixVisible = await page.getByText('Variant Stock Matrix').isVisible().catch(() => false);
  log('Variant matrix visible:', matrixVisible);
  await flush();

  // Canonical linear flow: Matrix -> Specs -> Finalize Listing (pricing).
  if (matrixVisible) {
    await page.getByRole('button', { name: /Done — Continue to Specs|Continue to Specs/ }).first().click().catch(e => log('matrix done click', e.message));
    await sleep(1200);
  }

  const specsVisible = await page.getByText('Product Specifications').isVisible().catch(() => false);
  log('Specs selector visible:', specsVisible);
  await flush();

  if (specsVisible) {
    await page.getByRole('button', { name: /Next — Finalize Listing|Finalize Listing/ }).first().click().catch(e => log('specs next click', e.message));
    await sleep(1200);
  }

  let pricingVisible = await page.getByText('Finalize Listing').isVisible().catch(() => false);
  if (!pricingVisible) {
    await page.getByRole('button', { name: /Review & Publish|Create & Next/ }).first().click().catch(() => {});
    await sleep(1500);
    pricingVisible = await page.getByText('Finalize Listing').isVisible().catch(() => false);
  }
  log('Pricing panel visible:', pricingVisible);
  await flush();

  const priceInput = page.locator('input[placeholder="0.000"]').first();
  let pv = await priceInput.inputValue().catch(() => '');
  log('Price before set:', JSON.stringify(pv));
  if (!pv) { await priceInput.fill('12.500'); }
  await sleep(300);

  const publishBtn = page.getByRole('button', { name: /Publish to Store/ });
  let publishStart = 0;
  if (await publishBtn.isVisible().catch(() => false)) {
    publishStart = Date.now();
    await publishBtn.click();
    log('Clicked Publish to Store');
  } else {
    const inline = page.getByRole('button', { name: /Review & Publish|Create & Next/ }).first();
    if (await inline.isVisible().catch(() => false)) { publishStart = Date.now(); await inline.click(); log('Clicked inline publish'); }
    else log('No publish button found');
  }
  // Poll for the success screen (publish POST can take several seconds).
  let success = false;
  for (let i = 0; i < 24; i++) {
    success = await page.getByText(/Product Published Successfully|PRODUCT PUBLISHED|published successfully|Listing Score|Thank you for using ZOZI/i).isVisible().catch(() => false);
    if (success) break;
    await sleep(500);
  }
  if (publishStart) log('Publish round-trip: ' + (Date.now() - publishStart) + 'ms (budget 20s)');
  await flush();

  log('Publish success screen visible:', success);
  await flush();

  log('--- ERRORS (' + errors.length + ') ---');
  errors.slice(0, 25).forEach(e => log(e));
  await flush();

  await browser.close();
  process.exit(0);
})().catch(async (e) => { console.error('TEST FAILED:', e.message); try { await browser.close(); } catch {}; process.exit(1); });
