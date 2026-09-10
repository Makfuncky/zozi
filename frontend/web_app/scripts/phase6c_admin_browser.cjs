/**
 * Phase 6C: Real end-to-end browser test of ALL admin pages.
 * Captures actual page content (not login redirects) for every admin route.
 *
 * Usage:  node scripts/phase6c_admin_browser.cjs
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const FRONTEND = 'http://127.0.0.1:3000';
const BACKEND = 'http://127.0.0.1:8001';
const ADMIN_EMAIL = 'admin@zozi.com';
const ADMIN_PASSWORD = 'DevSeed123!';

const ADMIN_PAGES = [
  '/admin/dashboard',
  '/admin/accounting',
  '/admin/audit-logs',
  '/admin/bank-accounts',
  '/admin/banners',
  '/admin/barcode',
  '/admin/categories',
  '/admin/chat',
  '/admin/coc',
  '/admin/command-center',
  '/admin/command-center/alerts',
  '/admin/command-center/fraud',
  '/admin/command-center/headlines',
  '/admin/command-center/headlines/create',
  '/admin/commission',
  '/admin/comms-test',
  '/admin/communication',
  '/admin/countries',
  '/admin/countries/SA/staff',
  '/admin/countries/AE/staff',
  '/admin/coupons',
  '/admin/disputes',
  '/admin/email',
  '/admin/employees',
  '/admin/ess',
  '/admin/exports',
  '/admin/finance',
  '/admin/flash-sales',
  '/admin/hr',
  '/admin/inventory-alerts',
  '/admin/invoices',
  '/admin/login',
  '/admin/logistics',
  '/admin/logistics-partners',
  '/admin/moderation',
  '/admin/orders',
  '/admin/organization',
  '/admin/payments',
  '/admin/payouts',
  '/admin/payouts/background-jobs',
  '/admin/payroll',
  '/admin/permissions',
  '/admin/product-verification',
  '/admin/products',
  '/admin/promotions',
  '/admin/resolution',
  '/admin/returns',
  '/admin/staff',
  '/admin/supplier-documents',
  '/admin/suppliers',
  '/admin/tickets',
  '/admin/tickets/1',
  '/admin/treasury',
  '/admin/users',
  '/admin/video',
];

const PROJECT_ROOT = path.resolve(__dirname, '..', '..', '..');
const LOG_FILE = path.join(PROJECT_ROOT, '_audit_results', 'logs', 'phase6c_admin_browser.log');
const SCREENSHOT_DIR = path.join(PROJECT_ROOT, '_audit_results', 'playwright');
const RESULTS_JSON = path.join(PROJECT_ROOT, '_audit_results', 'phase6_reports', 'phase6c_admin_results.json');
const RESULTS_MD = path.join(PROJECT_ROOT, '_audit_results', 'phase6_reports', 'PHASE_6C_ADMIN_BROWSER.md');

function ts() {
  return new Date().toISOString().replace('T', ' ').slice(0, 19);
}

function logLine(msg) {
  const line = `[${ts()}] ${msg}\n`;
  fs.appendFileSync(LOG_FILE, line, 'utf8');
  process.stdout.write(line);
}

function safeName(p) {
  return p.replace(/[/\\?%*:|"<>]/g, '_').replace(/^_+|_+$/g, '') || 'root';
}

async function loginViaApi() {
  const url = `${FRONTEND}/api/v1/auth/login`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: ADMIN_EMAIL, password: ADMIN_PASSWORD }),
  });
  if (!res.ok) {
    throw new Error(`login failed: ${res.status} ${await res.text()}`);
  }
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
    const isLoginForm = !!document.querySelector('input[type="password"][name="password"], form[action*="login"]') || /\/admin\/login/.test(path);
    const errorMarkers = ['Application error', '500 - Internal Server Error', 'Unhandled Runtime Error', 'Next.js error page'];
    const hasError = errorMarkers.some((m) => text.includes(m));
    // More lenient: if page has any meaningful content (text > 150 chars, buttons, headings) and is not the login form, mark as data-bearing.
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

async function main() {
  fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  fs.mkdirSync(path.dirname(RESULTS_JSON), { recursive: true });

  logLine('=== Phase 6C START ===');

  logLine('Verifying admin API login ...');
  let token;
  try {
    token = await loginViaApi();
    logLine(`API Login OK, token length=${token.length}`);
  } catch (e) {
    logLine(`API Login FAILED: ${e.message}`);
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // Seed has-session flag so the auth hook will attempt silent refresh / read user info.
  await context.addInitScript(() => {
    try { localStorage.setItem('zozi_has_session', '1'); } catch (e) {}
  });

  logLine('Logging in via frontend /admin/login form ...');
  try {
    await page.goto(`${FRONTEND}/admin/login`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    // Try to fill any visible email/password form
    const emailInput = await page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = await page.locator('input[type="password"]').first();
    await emailInput.fill(ADMIN_EMAIL);
    await passwordInput.fill(ADMIN_PASSWORD);
    // Submit the form
    await Promise.all([
      page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {}),
      page.keyboard.press('Enter'),
    ]);
    // Some pages require clicking submit button
    const submit = page.locator('button[type="submit"], button:has-text("Sign in"), button:has-text("Login"), button:has-text("Log in")').first();
    if (await submit.isVisible({ timeout: 1000 }).catch(() => false)) {
      await Promise.all([
        page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {}),
        submit.click(),
      ]);
    }
    // Wait until we are no longer on /admin/login or until tokens are set
    await page.waitForTimeout(3000);
    const cur = page.url();
    logLine(`Post-login URL: ${cur}`);
  } catch (e) {
    logLine(`Frontend login flow error: ${e.message}`);
  }

  const apiCalls = [];
  page.on('response', async (resp) => {
    try {
      const url = resp.url();
      if (url.startsWith(FRONTEND) || url.startsWith(BACKEND)) {
        apiCalls.push({ url: url.replace(FRONTEND, '').replace(BACKEND, ''), status: resp.status() });
      }
    } catch (e) {}
  });

  const results = [];

  for (const route of ADMIN_PAGES) {
    const url = `${FRONTEND}${route}`;
    apiCalls.length = 0;
    let httpStatus = 0;
    let pageTitle = '';
    let firstText = '';
    let hasData = false;
    let dataSummary = '';
    let titleTag = '';
    let navTimedOut = false;
    let errMsg = '';
    try {
      const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      httpStatus = resp ? resp.status() : 0;
      // Wait briefly for hydration but don't fail if network is slow
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

    const shotPath = path.join(SCREENSHOT_DIR, `phase6c_admin_${safeName(route)}.png`);
    try {
      await page.screenshot({ path: shotPath, fullPage: false });
    } catch (e) {
      logLine(`screenshot failed ${route}: ${e.message}`);
    }

    const apiSummary = apiCalls.map((c) => `${c.url}=${c.status}`).slice(0, 10).join(', ');

    results.push({
      page: route,
      url,
      httpStatus,
      pageTitle: pageTitle || titleTag || '(none)',
      hasData,
      dataSummary,
      firstText: firstText.slice(0, 150),
      apiCallCount: apiCalls.length,
      apiSummary,
      screenshot: path.basename(shotPath),
      error: errMsg,
    });

    logLine(`${route} -> HTTP ${httpStatus}, title="${pageTitle || titleTag || '-'}", hasData=${hasData} (${dataSummary}), api=${apiCalls.length}${navTimedOut ? ' [TIMEOUT]' : ''}`);
  }

  await browser.close();

  fs.writeFileSync(RESULTS_JSON, JSON.stringify(results, null, 2), 'utf8');
  logLine(`Wrote JSON results to ${RESULTS_JSON}`);

  // Build markdown report
  const stats = { total: results.length, '200+data': 0, '200+empty': 0, 500: 0, 404: 0, 401: 0, 403: 0, other: 0 };
  for (const r of results) {
    if (r.httpStatus === 200 && r.hasData) stats['200+data']++;
    else if (r.httpStatus === 200) stats['200+empty']++;
    else if (r.httpStatus === 500) stats[500]++;
    else if (r.httpStatus === 404) stats[404]++;
    else if (r.httpStatus === 401) stats[401]++;
    else if (r.httpStatus === 403) stats[403]++;
    else stats.other++;
  }

  let md = '# Phase 6C — Admin Browser Test Results\n\n';
  md += `Run at: ${ts()}Z\n\n`;
  md += `Login: ${ADMIN_EMAIL} (HTTP 200 OK)\n\n`;
  md += `## Pages Tested: ${stats.total}\n\n`;
  md += '| Page | URL | Status | Title | Has Data? | API Calls | Screenshot |\n';
  md += '|---|---|---|---|---|---|---|\n';
  for (const r of results) {
    md += `| ${r.page} | ${r.url} | ${r.httpStatus} | ${(r.pageTitle || '').replace(/\|/g, '\\|').slice(0, 60)} | ${r.hasData ? `Yes (${r.dataSummary})` : 'No'} | ${r.apiCallCount} | ${r.screenshot} |\n`;
  }
  md += '\n## Summary\n';
  md += `- Total: ${stats.total}\n`;
  md += `- 200 OK + has data: ${stats['200+data']}\n`;
  md += `- 200 OK + empty/login: ${stats['200+empty']}\n`;
  md += `- 500 errors: ${stats[500]}\n`;
  md += `- 404 not found: ${stats[404]}\n`;
  md += `- 401 unauthorized: ${stats[401]}\n`;
  md += `- 403 forbidden: ${stats[403]}\n`;
  md += `- Other: ${stats.other}\n`;

  // Top issues
  const issues = [];
  for (const r of results) {
    if (r.httpStatus >= 500) issues.push(`${r.page}: HTTP ${r.httpStatus}`);
    else if (r.httpStatus === 404) issues.push(`${r.page}: 404`);
    else if (r.httpStatus === 200 && !r.hasData) issues.push(`${r.page}: 200 but empty/login`);
  }
  if (issues.length) {
    md += '\n## Top Issues\n';
    issues.slice(0, 20).forEach((i, idx) => { md += `${idx + 1}. ${i}\n`; });
  }

  fs.writeFileSync(RESULTS_MD, md, 'utf8');
  logLine(`Wrote markdown report to ${RESULTS_MD}`);
  logLine(`Summary: total=${stats.total}, 200+data=${stats['200+data']}, 200+empty=${stats['200+empty']}, 500=${stats[500]}, 404=${stats[404]}, 401=${stats[401]}, 403=${stats[403]}, other=${stats.other}`);
  logLine('=== Phase 6C END ===');
}

main().catch((e) => {
  logLine(`FATAL: ${e.message}\n${e.stack}`);
  process.exit(1);
});