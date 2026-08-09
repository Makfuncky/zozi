const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const img = path.resolve(__dirname, '../../../image/image_05.jpg');

  const loginRes = await page.request.post('http://localhost:8000/auth/login', {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    form: { username: 'supplier@zozi.com', password: 'supplier123' },
  });
  const token = (await loginRes.json()).access_token;
  await page.goto('http://localhost:3000/supplier/products/add', { waitUntil: 'domcontentloaded' });
  await page.context().addCookies([{ name: 'access_token', value: token, url: 'http://localhost:3000' }]);
  await page.evaluate((t) => { localStorage.setItem('access_token', t); localStorage.setItem('zozi_has_session', '1'); }, token);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForSelector('text=New Product', { timeout: 15000 });
  const manual = page.getByText('Enter Manually');
  if (await manual.isVisible({ timeout: 3000 }).catch(() => false)) { await manual.click(); await page.waitForTimeout(500); }
  await page.waitForSelector('text=Choose Photo', { timeout: 15000 });

  const log = (m) => console.log(new Date().toISOString().slice(11,19), m);
  log('uploading');
  const input = page.locator('input[type="file"]').first();
  await input.setInputFiles(img);
  await input.evaluate((el) => { el.dispatchEvent(new Event('change', { bubbles: true })); });
  log('setInputFiles done');
  await page.locator('canvas').first().waitFor({ state: 'visible', timeout: 30000 }).then(() => log('canvas visible')).catch((e) => log('canvas ERR ' + e.message));
  await page.waitForTimeout(500);

  log('STEP: fast/quality toggle');
  const fastBtn = page.getByRole('button', { name: /fast|quality/i });
  if (await fastBtn.isVisible().catch(() => false)) {
    log('fastBtn visible, clicking');
    const fc = await fastBtn.count();
    log('fastBtn COUNT=' + fc);
    for (let i = 0; i < fc; i++) {
      const t = await fastBtn.nth(i).textContent().catch(() => '');
      log('  fastBtn[' + i + '] text="' + (t||'').trim() + '"');
    }
    await page.screenshot({ path: 'debug_before_fast.png' });
    await fastBtn.first().click({ timeout: 5000 }).then(() => log('clicked fast')).catch((e) => log('click ERR ' + e.message.split('\n')[0]));
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'debug_after_fast.png' });
  } else { log('fastBtn NOT visible'); }

  log('STEP: remove');
  const removeBtn = page.getByRole('button', { name: /remove/i });
  await removeBtn.first().waitFor({ state: 'visible', timeout: 5000 }).then(() => log('removeBtn visible')).catch((e) => log('removeBtn ERR ' + e.message));
  await removeBtn.first().click();
  await page.waitForTimeout(500);
  await page.getByText('Choose Photo').first().waitFor({ state: 'visible', timeout: 5000 }).then(() => log('Choose Photo visible')).catch((e) => log('ChoosePhoto ERR ' + e.message));

  log('DONE');
  await browser.close();
})();
