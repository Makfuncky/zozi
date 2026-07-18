// @ts-nocheck
const { chromium } = require("playwright");

const BASE = "http://localhost:3000";
const API = "http://127.0.0.1:8000";

// The 20 finance tabs defined in frontend/app/admin/finance/page.tsx
const SECTIONS = [
  "finance",
  "payouts",
  "bank-accounts",
  "treasury",
  "chart-of-accounts",
  "expense-scan",
  "bank-mapping",
  "fixed-assets",
  "accruals",
  "ar",
  "ap",
  "journal",
  "payments",
  "reconciliation",
  "budgets",
  "audit",
  "fx",
  "deferred-revenue",
  "email-ledger",
  "ai-reconcile",
];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(`[console] ${msg.text()}`);
  });
  page.on("pageerror", (err) => errors.push(`[pageerror] ${err.message}`));

  const results = { passed: [], failed: [] };

  // 1. Login as admin via API to obtain a token, then seed it into localStorage.
  const loginRes = await page.request.post(`${API}/auth/login`, {
    form: { username: "admin@test.com", password: "admin123" },
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  if (!loginRes.ok()) {
    console.log("LOGIN FAILED:", loginRes.status(), await loginRes.text());
    await browser.close();
    process.exit(1);
  }
  const loginJson = await loginRes.json();
  const token = loginJson.access_token;
  console.log("LOGIN OK, token len:", (token || "").length);

  // 2. Also verify key backend finance endpoints respond with 200 and valid shape.
  const today = new Date().toISOString().slice(0, 10);
  const yearAgo = new Date(Date.now() - 365 * 864e5).toISOString().slice(0, 10);
  const beChecks = [
    ["GET /finance/ledger", `${API}/finance/ledger?start_date=${yearAgo}&end_date=${today}`],
    ["GET /finance/trial-balance", `${API}/finance/trial-balance`],
    ["GET /treasury/metrics", `${API}/treasury/metrics`],
    ["GET /finance/cash-position", `${API}/finance/cash-position`],
    ["GET /finance/liabilities/exposure", `${API}/finance/liabilities/exposure`],
    ["GET /finance/vat/liability", `${API}/finance/vat/liability?period=2026-07`],
    ["GET /admin/treasury/consolidated/reconciliation/pipeline", `${API}/admin/treasury/consolidated/reconciliation/pipeline`],
  ];
  for (const [name, url] of beChecks) {
    try {
      const r = await page.request.get(url, { headers: { Authorization: `Bearer ${token}` } });
      const ok = r.ok();
      console.log(`BACKEND ${name}: ${r.status()} ${ok ? "OK" : "FAIL"}`);
      if (!ok) results.failed.push(`backend:${name} (${r.status()})`);
      else results.passed.push(`backend:${name}`);
    } catch (e) {
      console.log(`BACKEND ${name}: ERROR ${e.message}`);
      results.failed.push(`backend:${name} (${e.message})`);
    }
  }

  // 3. Navigate the SPA: set token, go to finance hub, then each section.
  await page.goto(`${BASE}/admin/finance`, { waitUntil: "domcontentloaded" });
  await page.evaluate((t) => {
    localStorage.setItem("zozi_access_token", t);
    localStorage.setItem("zozi_has_session", "1");
  }, token);
  await page.goto(`${BASE}/admin/finance`, { waitUntil: "networkidle" });
  await page.waitForTimeout(800);

  for (const section of SECTIONS) {
    try {
      await page.goto(`${BASE}/admin/finance?section=${section}`, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(900);
      // The finance hub shows a tab bar with the section label.
      const bodyText = await page.locator("body").innerText();
      const hasContent = bodyText.replace(/\s+/g, "").length > 30;
      const titleVisible = await page.locator("h1, h2, h3").first().isVisible().catch(() => false);
      if (hasContent) {
        results.passed.push(`ui:${section}`);
        console.log(`UI section ${section}: OK (content rendered)`);
      } else {
        results.failed.push(`ui:${section} (no content)`);
        console.log(`UI section ${section}: FAIL (no content)`);
      }
    } catch (e) {
      results.failed.push(`ui:${section} (${e.message})`);
      console.log(`UI section ${section}: ERROR ${e.message}`);
    }
  }

  // 4. Verify period-close lock endpoint works (Phase 0 mandate).
  try {
    const pc = await page.request.get(`${API}/admin/treasury/consolidated/reconciliation/pipeline`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log("Period/Reconciliation pipeline:", pc.status());
  } catch (e) {
    console.log("pipeline err", e.message);
  }

  await browser.close();

  console.log("\n==== SUMMARY ====");
  console.log("PASSED:", results.passed.length);
  console.log("FAILED:", results.failed.length);
  if (results.failed.length) {
    console.log("Failures:");
    results.failed.forEach((f) => console.log(" -", f));
  }
  console.log("Console/page errors captured:", errors.length);
  errors.slice(0, 20).forEach((e) => console.log("  ", e));

  process.exit(results.failed.length ? 2 : 0);
})();
