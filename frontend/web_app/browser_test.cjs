const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

function findChromium() {
  const base = path.join(process.env.USERPROFILE, 'AppData', 'Local', 'ms-playwright');
  if (!fs.existsSync(base)) return undefined;
  const dirs = fs.readdirSync(base).filter(d => /^chromium-\d+$/.test(d));
  dirs.sort((a, b) => parseInt(a.split('-')[1], 10) - parseInt(b.split('-')[1], 10));
  for (const d of dirs.reverse()) {
    const p = path.join(base, d, 'chrome-win', 'chrome.exe');
    if (fs.existsSync(p)) return p;
  }
  return undefined;
}

(async () => {
  const exe = findChromium();
  const browser = await chromium.launch({ headless: true, executablePath: exe, args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

  const consoleMsgs = [];
  const pageErrors = [];
  const apiCalls = [];
  page.on('console', m => consoleMsgs.push({ type: m.type(), text: m.text() }));
  page.on('pageerror', e => pageErrors.push(String(e && e.stack ? e.stack : e)));

  const isApi = u => /127\.0\.0\.1:8000/.test(u) || /^\/(api|auth|admin|__api|uploads|hr)\//.test(u);
  page.on('response', r => {
    const u = r.url();
    if (isApi(u)) apiCalls.push({ url: u.replace('http://127.0.0.1:3000', ''), status: r.status(), method: r.request().method() });
  });
  page.on('requestfailed', r => {
    const u = r.url();
    if (isApi(u)) apiCalls.push({ url: u.replace('http://127.0.0.1:3000', ''), status: 'FAILED', error: (r.failure() || {}).errorText });
  });

  const result = { homepage: {}, login: {}, summary: {} };

  // ---- Homepage ----
  try {
    const resp = await page.goto('http://127.0.0.1:3000/', { waitUntil: 'load', timeout: 60000 });
    result.homepage.status = resp && resp.status();
    result.homepage.title = await page.title();
    await page.waitForTimeout(3500);
    result.homepage.bodySample = (await page.textContent('body') || '').replace(/\s+/g, ' ').slice(0, 400);
    result.homepage.hasZoziText = /ZOZI/i.test(await page.textContent('body') || '');
  } catch (e) { result.homepage.error = String(e); }

  result.homepage.apiCalls = apiCalls.slice();

  // ---- Login attempt ----
  apiCalls.length = 0;
  try {
    await page.goto('http://127.0.0.1:3000/login', { waitUntil: 'load', timeout: 60000 });
    await page.waitForSelector('input[placeholder="you@email.com"]', { timeout: 15000 });
    await page.fill('input[placeholder="you@email.com"]', 'customer@zozi.com');
    await page.fill('input[placeholder="••••••••"]', 'customer123');
    const [loginResp] = await Promise.all([
      page.waitForResponse(r => r.url().includes('/auth/login'), { timeout: 30000 }).catch(() => null),
      page.click('button:has-text("Sign In")'),
    ]);
    await page.waitForTimeout(2500);
    result.login.responseStatus = loginResp ? loginResp.status() : 'no-response';
    try { result.login.responseBody = loginResp ? (await loginResp.json()) : null; } catch (e) { result.login.responseBody = (await loginResp.text().catch(() => null)); }
    result.login.visibleError = await page.evaluate(() => {
      const d = document.querySelector('.theme-alert-danger');
      return d ? d.textContent.trim() : null;
    });
    result.login.stillOnLogin = /Sign In/i.test(await page.textContent('body') || '');
    result.login.apiCalls = apiCalls.slice();
  } catch (e) { result.login.error = String(e); }

  result.summary = {
    consoleErrors: consoleMsgs.filter(m => m.type === 'error'),
    consoleWarnings: consoleMsgs.filter(m => m.type === 'warning').slice(0, 10),
    pageErrors,
    totalApiCalls: apiCalls.length,
  };

  console.log('=====BROWSER_TEST_RESULT=====');
  console.log(JSON.stringify(result, null, 2));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
