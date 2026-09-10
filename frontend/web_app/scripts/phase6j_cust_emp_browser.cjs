/**
 * Phase 6J: Real end-to-end browser test of ALL customer + employee pages.
 * Captures actual page content for every customer and employee route.
 *
 * Usage:  node scripts/phase6j_cust_emp_browser.cjs
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const FRONTEND = 'http://127.0.0.1:3000';
const BACKEND = 'http://127.0.0.1:8000';
const CUSTOMER_EMAIL = 'customer@zozi.com';
const CUSTOMER_PASSWORD = 'DevSeed123!';
const EMPLOYEE_EMAIL = 'employee@zozi.com';
const EMPLOYEE_PASSWORD = 'DevSeed123!';

const CUSTOMER_PAGES = [
  '/', '/login', '/register', '/verify-email', '/reset-password', '/auth/callback',
  '/products', '/products/category', '/products/1',
  '/cart', '/checkout',
  '/orders', '/orders/1',
  '/wishlist', '/brand', '/archive',
  '/invoice', '/returns', '/returns/1', '/tracking/1',
  '/profile', '/profile/referrals',
  '/notifications', '/offers', '/contact', '/help',
  '/barcode-scan', '/chatbot',
  '/newsletter/preferences', '/newsletter/unsubscribe',
  '/logo-animation', '/meet/demo',
];

const EMPLOYEE_PAGES = [
  '/employee', '/employee/login', '/employee/dashboard',
  '/employee/attendance', '/employee/documents', '/employee/leaves',
  '/employee/notifications', '/employee/payroll', '/employee/performance',
  '/employee/profile', '/employee/schedule', '/employee/training',
  '/employee/workspace', '/employee/workspace/tasks',
];

const PROJECT_ROOT = path.resolve(__dirname, '..', '..', '..');
const LOG_FILE = path.join(PROJECT_ROOT, '_audit_results', 'logs', 'phase6j_cust_emp_browser.log');
const SCREENSHOT_DIR = path.join(PROJECT_ROOT, '_audit_results', 'playwright');
const RESULTS_JSON = path.join(PROJECT_ROOT, '_audit_results', 'phase6_reports', 'phase6j_results.json');
const RESULTS_MD = path.join(PROJECT_ROOT, '_audit_results', 'phase6_reports', 'PHASE_6J_CUST_EMP_BROWSER.md');

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

async function loginViaApi(email, password) {
  const url = `${FRONTEND}/api/v1/auth/login`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
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
    const isLoginForm = !!document.querySelector('input[type="password"][name="password"], form[action*="login"]') || /\/login/.test(path);
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

async function visitPages(page, browser, pages, prefix, loginEmail, loginPassword, loginFormSelector, loginPath) {
  const context = browser.contexts()[0] || await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const results = [];

  const apiCalls = [];
  page.on('response', async (resp) => {
    try {
      const url = resp.url();
      if (url.startsWith(FRONTEND) || url.startsWith(BACKEND)) {
        apiCalls.push({ url: url.replace(FRONTEND, '').replace(BACKEND, ''), status: resp.status() });
      }
    } catch (e) {}
  });

  logLine(`Logging in via frontend ${loginPath} ...`);
  try {
    await page.goto(`${FRONTEND}${loginPath}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    const emailInput = await page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = await page.locator('input[type="password"]').first();
    if (await emailInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await emailInput.fill(loginEmail);
      await passwordInput.fill(loginPassword);
      await Promise.all([
        page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {}),
        page.keyboard.press('Enter'),
      ]);
      const submit = page.locator('button[type="submit"], button:has-text("Sign in"), button:has-text("Login"), button:has-text("Log in")').first();
      if (await submit.isVisible({ timeout: 1000 }).catch(() => false)) {
        await Promise.all([
          page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {}),
          submit.click(),
        ]);
      }
      await page.waitForTimeout(3000);
    }
    logLine(`Post-login URL: ${page.url()}`);
  } catch (e) {
    logLine(`Frontend login flow error: ${e.message}`);
  }

  for (const route of pages) {
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

    const shotPath = path.join(SCREENSHOT_DIR, `phase6j_${prefix}_${safeName(route)}.png`);
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

    logLine(`${prefix} ${route} -> HTTP ${httpStatus}, title="${pageTitle || titleTag || '-'}", hasData=${hasData} (${dataSummary}), api=${apiCalls.length}${navTimedOut ? ' [TIMEOUT]' : ''}`);
  }

  return results;
}

async function main() {
  fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  fs.mkdirSync(path.dirname(RESULTS_JSON), { recursive: true });

  logLine('=== Phase 6J START ===');

  // ----- CUSTOMER -----
  logLine('Verifying customer API login ...');
  let customerToken;
  try {
    customerToken = await loginViaApi(CUSTOMER_EMAIL, CUSTOMER_PASSWORD);
    logLine(`Customer API Login OK, token length=${customerToken.length}`);
  } catch (e) {
    logLine(`Customer API Login FAILED: ${e.message}`);
  }

  const browser = await chromium.launch({ headless: true });
  const customerCtx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await customerCtx.addInitScript(() => {
    try { localStorage.setItem('zozi_has_session', '1'); } catch (e) {}
  });
  const customerPage = await customerCtx.newPage();
  const customerResults = await visitPages(customerPage, browser, CUSTOMER_PAGES, 'customer', CUSTOMER_EMAIL, CUSTOMER_PASSWORD, null, '/login');
  await customerCtx.close();

  // ----- EMPLOYEE -----
  logLine('Verifying employee API login ...');
  let employeeToken;
  try {
    employeeToken = await loginViaApi(EMPLOYEE_EMAIL, EMPLOYEE_PASSWORD);
    logLine(`Employee API Login OK, token length=${employeeToken.length}`);
  } catch (e) {
    logLine(`Employee API Login FAILED: ${e.message}`);
  }

  const employeeCtx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await employeeCtx.addInitScript(() => {
    try { localStorage.setItem('zozi_has_session', '1'); } catch (e) {}
  });
  const employeePage = await employeeCtx.newPage();
  const employeeResults = await visitPages(employeePage, browser, EMPLOYEE_PAGES, 'employee', EMPLOYEE_EMAIL, EMPLOYEE_PASSWORD, null, '/employee/login');
  await employeeCtx.close();

  await browser.close();

  const all = { customer: customerResults, employee: employeeResults };
  fs.writeFileSync(RESULTS_JSON, JSON.stringify(all, null, 2), 'utf8');
  logLine(`Wrote JSON results to ${RESULTS_JSON}`);

  function stats(rs) {
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
  const cs = stats(customerResults);
  const es = stats(employeeResults);

  let md = '# Phase 6J — Customer + Employee Browser Test Results\n\n';
  md += `Run at: ${ts()}Z\n\n`;
  md += `Backend on ${BACKEND}, frontend on ${FRONTEND}.\n\n`;
  md += `Customer login: ${CUSTOMER_EMAIL}\n`;
  md += `Employee login: ${EMPLOYEE_EMAIL}\n\n`;

  md += `## Customer Browser Test Results\n\n`;
  md += `Pages tested: ${cs.total}\n\n`;
  md += '| Page | URL | Status | Title | Has Data? | API Calls | Screenshot |\n';
  md += '|---|---|---|---|---|---|---|\n';
  for (const r of customerResults) {
    md += `| ${r.page} | ${r.url} | ${r.httpStatus} | ${(r.pageTitle || '').replace(/\|/g, '\\|').slice(0, 60)} | ${r.hasData ? `Yes (${r.dataSummary})` : 'No'} | ${r.apiCallCount} | ${r.screenshot} |\n`;
  }
  md += `\n## Customer Summary\n`;
  md += `- Total: ${cs.total}\n`;
  md += `- 200 OK + has data: ${cs['200+data']}\n`;
  md += `- 200 OK + empty/login: ${cs['200+empty']}\n`;
  md += `- 500 errors: ${cs[500]}\n`;
  md += `- 404 not found: ${cs[404]}\n`;
  md += `- 401 unauthorized: ${cs[401]}\n`;
  md += `- 403 forbidden: ${cs[403]}\n`;
  md += `- Other: ${cs.other}\n`;

  md += `\n## Employee Browser Test Results\n\n`;
  md += `Pages tested: ${es.total}\n\n`;
  md += '| Page | URL | Status | Title | Has Data? | API Calls | Screenshot |\n';
  md += '|---|---|---|---|---|---|---|\n';
  for (const r of employeeResults) {
    md += `| ${r.page} | ${r.url} | ${r.httpStatus} | ${(r.pageTitle || '').replace(/\|/g, '\\|').slice(0, 60)} | ${r.hasData ? `Yes (${r.dataSummary})` : 'No'} | ${r.apiCallCount} | ${r.screenshot} |\n`;
  }
  md += `\n## Employee Summary\n`;
  md += `- Total: ${es.total}\n`;
  md += `- 200 OK + has data: ${es['200+data']}\n`;
  md += `- 200 OK + empty/login: ${es['200+empty']}\n`;
  md += `- 500 errors: ${es[500]}\n`;
  md += `- 404 not found: ${es[404]}\n`;
  md += `- 401 unauthorized: ${es[401]}\n`;
  md += `- 403 forbidden: ${es[403]}\n`;
  md += `- Other: ${es.other}\n`;

  // Issues
  const issues = [];
  for (const r of [...customerResults, ...employeeResults]) {
    if (r.httpStatus >= 500) issues.push(`${r.page}: HTTP ${r.httpStatus}`);
    else if (r.httpStatus === 404) issues.push(`${r.page}: 404`);
    else if (r.httpStatus === 200 && !r.hasData) issues.push(`${r.page}: 200 but empty/login`);
  }
  if (issues.length) {
    md += `\n## Issues (${issues.length})\n`;
    issues.slice(0, 40).forEach((i, idx) => { md += `${idx + 1}. ${i}\n`; });
  }

  fs.writeFileSync(RESULTS_MD, md, 'utf8');
  logLine(`Wrote markdown report to ${RESULTS_MD}`);
  logLine(`Customer Summary: total=${cs.total}, 200+data=${cs['200+data']}, 200+empty=${cs['200+empty']}, 500=${cs[500]}, 404=${cs[404]}`);
  logLine(`Employee Summary: total=${es.total}, 200+data=${es['200+data']}, 200+empty=${es['200+empty']}, 500=${es[500]}, 404=${es[404]}`);
  logLine('=== Phase 6J END ===');
}

main().catch((e) => {
  logLine(`FATAL: ${e.message}\n${e.stack}`);
  process.exit(1);
});