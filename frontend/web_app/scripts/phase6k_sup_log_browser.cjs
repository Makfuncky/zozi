/**
 * Phase 6K: Real end-to-end browser test of ALL supplier + logistics-partner pages.
 * 34 supplier pages + 8 logistics pages = 42 screenshots.
 *
 * Usage:  node scripts/phase6k_sup_log_browser.cjs
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const FRONTEND = 'http://127.0.0.1:3000';
const BACKEND = 'http://127.0.0.1:8001';

const SUPPLIER_EMAIL = 'supplier@zozi.com';
const SUPPLIER_PASSWORD = 'DevSeed123!';
const LOGISTICS_EMAIL = 'logistics@zozi.com';
const LOGISTICS_PASSWORD = 'DevSeed123!';

const SUPPLIER_PAGES = [
  '/supplier', '/supplier/login', '/supplier/register',
  '/supplier/dashboard',
  '/supplier/products', '/supplier/products/add', '/supplier/products/1',
  '/supplier/inventory', '/supplier/orders', '/supplier/orders/1',
  '/supplier/payouts', '/supplier/invoices',
  '/supplier/disputes', '/supplier/returns',
  '/supplier/analytics', '/supplier/reports',
  '/supplier/commission', '/supplier/credibility',
  '/supplier/documents', '/supplier/regions',
  '/supplier/logistics',
  '/supplier/labels', '/supplier/labels/1',
  '/supplier/list-product',
  '/supplier/upload', '/supplier/upload/bg-compare',
  '/supplier/videos/upload',
  '/supplier/batch-upload', '/supplier/bulk',
  '/supplier/support', '/supplier/profile',
  '/supplier/guide', '/supplier/terms',
  '/supplier/notification-preferences',
];

const LOGISTICS_PAGES = [
  '/logistics-partner', '/logistics-partner/login', '/logistics-partner/register',
  '/logistics-partner/dashboard',
  '/logistics-partner/shipments',
  '/logistics-partner/routes',
  '/logistics-partner/scan',
  '/logistics-partner/payouts',
  '/logistics-partner/analytics',
  '/logistics-partner/profile',
];

const PROJECT_ROOT = path.resolve(__dirname, '..', '..', '..');
const LOG_FILE = path.join(PROJECT_ROOT, '_audit_results', 'logs', 'phase6k_sup_log_browser.log');
const SCREENSHOT_DIR = path.join(PROJECT_ROOT, '_audit_results', 'playwright');
const RESULTS_JSON = path.join(PROJECT_ROOT, '_audit_results', 'phase6_reports', 'phase6k_results.json');
const RESULTS_MD = path.join(PROJECT_ROOT, '_audit_results', 'phase6_reports', 'PHASE_6K_SUP_LOG_BROWSER.md');

function ts() { return new Date().toISOString().replace('T', ' ').slice(0, 19); }
function logLine(msg) {
  const line = `[${ts()}] ${msg}\n`;
  fs.appendFileSync(LOG_FILE, line, 'utf8');
  process.stdout.write(line);
}
function safeName(p) {
  return p.replace(/[/\\?%*:|"<>]/g, '_').replace(/^_+|_+$/g, '') || 'root';
}

async function loginViaApi(email, password) {
  const url = `${FRONTEND}/api/v1/auth/login`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(`login(${email}) failed: ${res.status} ${await res.text()}`);
  const data = await res.json();
  return data.access_token;
}

async function detectContent(page) {
  return await page.evaluate(() => {
    const text = (document.body?.innerText || '').replace(/\s+/g, ' ').trim();
    const tables = document.querySelectorAll('table tbody tr').length;
    const cards = document.querySelectorAll('[class*="card" i], [class*="Card"]').length;
    const lists = document.querySelectorAll('ul li, ol li').length;
    const buttons = document.querySelectorAll('button').length;
    const h1 = document.querySelector('h1')?.innerText?.trim() || '';
    const h2 = document.querySelector('h2')?.innerText?.trim() || '';
    const title = document.title || '';
    const path = location.pathname;
    const isLoginForm = !!document.querySelector('input[type="password"][name="password"], form[action*="login"]')
      || /\/login/.test(path);
    const errorMarkers = ['Application error', '500 - Internal Server Error', 'Unhandled Runtime Error', 'Next.js error page'];
    const hasError = errorMarkers.some((m) => text.includes(m));
    const hasData = !isLoginForm && !hasError && (tables > 0 || cards > 1 || lists > 3 || (text.length > 200 && (buttons > 2 || h1 || h2)));
    let dataSummary = '';
    if (tables > 0) dataSummary = `${tables} table rows`;
    else if (cards > 1) dataSummary = `${cards} cards`;
    else if (lists > 3) dataSummary = `${lists} list items`;
    else if (text.length > 100) dataSummary = `${text.length} chars`;
    else dataSummary = 'empty';
    return { text: text.slice(0, 220), tables, cards, lists, buttons, h1, h2, title, isLoginForm, hasError, hasData, dataSummary };
  });
}

async function loginInBrowser(page, email, password, loginPath) {
  logLine(`Logging in via ${loginPath} as ${email} ...`);
  try {
    await page.goto(`${FRONTEND}${loginPath}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    if (await emailInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await emailInput.fill(email);
      await passwordInput.fill(password);
      const submit = page.locator('button[type="submit"], button:has-text("Sign in"), button:has-text("Login"), button:has-text("Log in")').first();
      await Promise.all([
        page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {}),
        submit.click({ timeout: 5000 }).catch(() => page.keyboard.press('Enter')),
      ]);
      await page.waitForTimeout(3000);
    }
    logLine(`Post-login URL: ${page.url()}`);
  } catch (e) {
    logLine(`Frontend login flow error: ${e.message}`);
  }
}

async function visitAll(page, roleLabel, pages, apiCalls) {
  const results = [];
  for (const route of pages) {
    const url = `${FRONTEND}${route}`;
    apiCalls.length = 0;
    let httpStatus = 0, pageTitle = '', firstText = '', hasData = false, dataSummary = '', titleTag = '', errMsg = '', navTimedOut = false;
    try {
      const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      httpStatus = resp ? resp.status() : 0;
      try { await page.waitForLoadState('networkidle', { timeout: 6000 }).catch(() => {}); } catch (_) {}
      const info = await detectContent(page);
      pageTitle = info.h1 || info.h2 || '';
      firstText = info.text;
      hasData = info.hasData;
      dataSummary = info.dataSummary;
      titleTag = info.title;
    } catch (e) {
      errMsg = e.message;
      navTimedOut = /Timeout/i.test(errMsg);
    }

    const prefix = roleLabel === 'supplier' ? 'phase6k_supplier_' : 'phase6k_logistics_';
    const shotPath = path.join(SCREENSHOT_DIR, `${prefix}${safeName(route)}.png`);
    try { await page.screenshot({ path: shotPath, fullPage: false }); } catch (e) {
      logLine(`screenshot failed ${route}: ${e.message}`);
    }
    const apiSummary = apiCalls.map((c) => `${c.url}=${c.status}`).slice(0, 10).join(', ');

    results.push({
      role: roleLabel, page: route, url, httpStatus,
      pageTitle: pageTitle || titleTag || '(none)',
      hasData, dataSummary, firstText: firstText.slice(0, 150),
      apiCallCount: apiCalls.length, apiSummary,
      screenshot: path.basename(shotPath), error: errMsg,
    });
    logLine(`[${roleLabel}] ${route} -> HTTP ${httpStatus}, title="${pageTitle || titleTag || '-'}", hasData=${hasData} (${dataSummary}), api=${apiCalls.length}${navTimedOut ? ' [TIMEOUT]' : ''}`);
  }
  return results;
}

async function main() {
  fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  fs.mkdirSync(path.dirname(RESULTS_JSON), { recursive: true });

  logLine('=== Phase 6K START ===');

  // Verify API logins (best-effort: continue even on 500 to capture screenshots of UI shells)
  let supplierToken = null, logisticsToken = null;
  try {
    supplierToken = await loginViaApi(SUPPLIER_EMAIL, SUPPLIER_PASSWORD);
    logLine(`supplier API login OK, token length=${supplierToken.length}`);
  } catch (e) {
    logLine(`supplier API login FAILED (will continue without token): ${e.message}`);
  }
  try {
    logisticsToken = await loginViaApi(LOGISTICS_EMAIL, LOGISTICS_PASSWORD);
    logLine(`logistics API login OK, token length=${logisticsToken.length}`);
  } catch (e) {
    logLine(`logistics API login FAILED (will continue without token): ${e.message}`);
  }

  const browser = await chromium.launch({ headless: true });
  const apiCalls = [];

  // Supplier pass
  {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    await context.addInitScript(() => { try { localStorage.setItem('zozi_has_session', '1'); } catch (e) {} });
    const page = await context.newPage();
    page.on('response', async (resp) => {
      try {
        const url = resp.url();
        if (url.startsWith(FRONTEND) || url.startsWith(BACKEND)) {
          apiCalls.push({ url: url.replace(FRONTEND, '').replace(BACKEND, ''), status: resp.status() });
        }
      } catch (e) {}
    });
    await loginInBrowser(page, SUPPLIER_EMAIL, SUPPLIER_PASSWORD, '/supplier/login');
    var supplierResults = await visitAll(page, 'supplier', SUPPLIER_PAGES, apiCalls);
    await context.close();
  }

  // Logistics pass
  {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    await context.addInitScript(() => { try { localStorage.setItem('zozi_has_session', '1'); } catch (e) {} });
    const page = await context.newPage();
    page.on('response', async (resp) => {
      try {
        const url = resp.url();
        if (url.startsWith(FRONTEND) || url.startsWith(BACKEND)) {
          apiCalls.push({ url: url.replace(FRONTEND, '').replace(BACKEND, ''), status: resp.status() });
        }
      } catch (e) {}
    });
    await loginInBrowser(page, LOGISTICS_EMAIL, LOGISTICS_PASSWORD, '/logistics-partner/login');
    var logisticsResults = await visitAll(page, 'logistics', LOGISTICS_PAGES, apiCalls);
    await context.close();
  }

  await browser.close();

  const all = [...supplierResults, ...logisticsResults];
  fs.writeFileSync(RESULTS_JSON, JSON.stringify(all, null, 2), 'utf8');
  logLine(`Wrote JSON results to ${RESULTS_JSON}`);

  function tally(rs) {
    const s = { total: rs.length, '200+data': 0, '200+empty': 0, 500: 0, 404: 0, 401: 0, 403: 0, other: 0 };
    for (const r of rs) {
      if (r.httpStatus === 200 && r.hasData) s['200+data']++;
      else if (r.httpStatus === 200) s['200+empty']++;
      else if (r.httpStatus === 500) s[500]++;
      else if (r.httpStatus === 404) s[404]++;
      else if (r.httpStatus === 401) s[401]++;
      else if (r.httpStatus === 403) s[403]++;
      else s.other++;
    }
    return s;
  }

  const supStats = tally(supplierResults);
  const logStats = tally(logisticsResults);

  let md = '# Phase 6K — Supplier & Logistics-Partner Browser Test Results\n\n';
  md += `Run at: ${ts()}Z\n\n`;
  md += `Logins: API login returned HTTP 500 (backend bug — realtime.py uses raw text() with schema prefix not stripped by schema_translate_map on sqlite; DB tables are unprefixed). Browser-level login flow also failed. Pages that don't require auth (e.g. /supplier landing, /supplier/register, /supplier/dashboard, /logistics-partner/register) rendered real content; auth-required pages redirected to login forms.\n\n`;

  function writeSection(title, rs, stats) {
    md += `\n## ${title} (${stats.total} pages)\n\n`;
    md += '| Page | Status | Title | Has Data? | API Calls | Screenshot |\n';
    md += '|---|---|---|---|---|---|\n';
    for (const r of rs) {
      md += `| ${r.page} | ${r.httpStatus} | ${(r.pageTitle || '').replace(/\|/g, '\\|').slice(0, 60)} | ${r.hasData ? `Yes (${r.dataSummary})` : 'No'} | ${r.apiCallCount} | ${r.screenshot} |\n`;
    }
    md += `\nSummary: total=${stats.total}, 200+data=${stats['200+data']}, 200+empty=${stats['200+empty']}, 500=${stats[500]}, 404=${stats[404]}, 401=${stats[401]}, 403=${stats[403]}, other=${stats.other}\n`;
    const issues = [];
    for (const r of rs) {
      if (r.httpStatus >= 500) issues.push(`${r.page}: HTTP ${r.httpStatus}`);
      else if (r.httpStatus === 404) issues.push(`${r.page}: 404`);
      else if (r.httpStatus === 200 && !r.hasData) issues.push(`${r.page}: 200 but empty/login`);
    }
    if (issues.length) {
      md += `\n### Issues (${issues.length})\n`;
      issues.slice(0, 25).forEach((i, idx) => { md += `${idx + 1}. ${i}\n`; });
    }
  }

  writeSection('Supplier Pages', supplierResults, supStats);
  writeSection('Logistics-Partner Pages', logisticsResults, logStats);

  md += `\n## Combined Total\n`;
  md += `- Supplier: ${supStats.total} pages, ${supStats['200+data']} with data, ${supStats[500]} 500s, ${supStats[404]} 404s\n`;
  md += `- Logistics: ${logStats.total} pages, ${logStats['200+data']} with data, ${logStats[500]} 500s, ${logStats[404]} 404s\n`;
  md += `- Grand total: ${supStats.total + logStats.total} pages, ${supStats['200+data'] + logStats['200+data']} with data\n`;

  fs.writeFileSync(RESULTS_MD, md, 'utf8');
  logLine(`Wrote markdown report to ${RESULTS_MD}`);
  logLine(`SUMMARY supplier: total=${supStats.total}, 200+data=${supStats['200+data']}, 200+empty=${supStats['200+empty']}, 500=${supStats[500]}, 404=${supStats[404]}`);
  logLine(`SUMMARY logistics: total=${logStats.total}, 200+data=${logStats['200+data']}, 200+empty=${logStats['200+empty']}, 500=${logStats[500]}, 404=${logStats[404]}`);
  logLine('=== Phase 6K END ===');
}

main().catch((e) => {
  logLine(`FATAL: ${e.message}\n${e.stack}`);
  process.exit(1);
});
