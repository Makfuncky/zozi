/**
 * Admin journey — platform operations and the finance business logic.
 *
 * Covers the operator surfaces: command centre telemetry, user/tenant
 * administration, the per-country control plane, commission configuration, and
 * the finance ledger tabs (COA, journal, budgets, AR/AP, bank mapping).
 */
import { test } from "@playwright/test";
import { bootstrapAdminSessionViaApi, submitCredentialForm, waitForSessionFlag } from "../../src/auth";
import { step, settle, collectDiagnostics } from "../../src/evidence";
import { JourneyLog, clickAny, fillAny, countRows, waitForContent } from "../../src/journey";

const ACTOR = "admin";
const SEED = process.env.SEED_ADMIN_PASSWORD || "E2eAdmin#2026";

test.describe.configure({ timeout: 3_600_000 });

test("admin: platform operations and finance journey", async ({ page }) => {
  const log = new JourneyLog();
  const seeded = await bootstrapAdminSessionViaApi(page);
  log.record("session", seeded ? "api bootstrap" : "api bootstrap failed", seeded ? "ok" : "error");
  if (!seeded) {
    await page.goto("/admin/login", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await submitCredentialForm(page, "admin@zozi.com", SEED);
    await waitForSessionFlag(page);
  }

  // ── Command centre: live telemetry ────────────────────────────────────
  await step(page, ACTOR, "command-center", async () => {
    await page.goto("/admin/command-center", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await settle(page, { budgetMs: 50_000 });
  });
  log.record("command-center", "panels", (await countRows(page)) > 0 ? "ok" : "not-found", `${await countRows(page)} rows`);

  for (const [name, path] of [
    ["command-center-fraud", "/admin/command-center/fraud"],
    ["command-center-alerts", "/admin/command-center/alerts"],
    ["command-center-headlines", "/admin/command-center/headlines"],
  ] as const) {
    await step(page, ACTOR, name, async () => {
      await page.goto(path, { waitUntil: "domcontentloaded", timeout: 60_000 });
      await settle(page, { budgetMs: 35_000 });
    });
  }

  // ── Tenancy & users ───────────────────────────────────────────────────
  await step(page, ACTOR, "users", async () => {
    await page.goto("/admin/users", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await waitForContent(page, ['table tbody tr', '[role="row"]'], 45_000);
  });
  const userRows = await countRows(page);
  log.record("users", "user rows", userRows > 0 ? "ok" : "not-found", `${userRows} rows`);

  await step(page, ACTOR, "user-search", () =>
    fillAny(page, ['input[name*="search" i]', 'input[placeholder*="search" i]', 'input[type="search"]'], "zozi.com", log, "users"),
  );

  await step(page, ACTOR, "permissions-matrix", async () => {
    await page.goto("/admin/permissions", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  // ── Country control plane ─────────────────────────────────────────────
  await step(page, ACTOR, "countries", async () => {
    await page.goto("/admin/countries", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await waitForContent(page, ['[data-testid="country-ledger-row-AE"]', "table tbody tr"], 45_000);
  });
  await step(page, ACTOR, "country-select-oman", async () => {
    const row = page.locator('[data-testid="country-ledger-row-OM"]').first();
    if (await row.isVisible({ timeout: 6_000 }).catch(() => false)) {
      await row.click({ timeout: 8_000 }).catch(() => {});
      log.record("country-select-oman", "expand ledger row", "ok");
    } else {
      log.record("country-select-oman", "expand ledger row", "not-found");
    }
  });
  for (const tab of ["Commission", "Payouts", "FX", "Users", "Governance"]) {
    await step(page, ACTOR, `country-tab-${tab.toLowerCase()}`, () =>
      clickAny(page, [{ role: "button", name: new RegExp(tab, "i") }, { role: "tab", name: new RegExp(tab, "i") }, { text: new RegExp(`^${tab}$`, "i") }], log, `country-tab-${tab}`),
    );
  }

  // ── Commission configuration (business logic) ─────────────────────────
  await step(page, ACTOR, "commission", async () => {
    await page.goto("/admin/commission", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await settle(page, { budgetMs: 35_000 });
  });
  await step(page, ACTOR, "commission-edit-rate", async () => {
    const edit = await page.getByRole("button", { name: /edit|modify/i }).first();
    if (await edit.isVisible({ timeout: 6_000 }).catch(() => false)) {
      await edit.click({ timeout: 8_000 }).catch(() => {});
      log.record("commission-edit-rate", "open editor", "ok");
    } else {
      log.record("commission-edit-rate", "open editor", "not-found");
    }
  });

  // ── Finance ledger ────────────────────────────────────────────────────
  await step(page, ACTOR, "finance-hub", async () => {
    await page.goto("/admin/finance", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await settle(page, { budgetMs: 40_000 });
  });
  for (const tab of ["coa", "fx", "deferred-revenue", "email-to-ledger", "bank-mapping", "ar-ap", "journal", "budgets", "audit-log"]) {
    await step(page, ACTOR, `finance-${tab}`, async () => {
      await page.goto(`/admin/finance?tab=${tab}`, { waitUntil: "domcontentloaded", timeout: 60_000 });
      await settle(page, { budgetMs: 30_000 });
    });
  }

  // ── Orders, disputes, returns (operations) ────────────────────────────
  for (const [name, path] of [
    ["orders", "/admin/orders"],
    ["disputes", "/admin/disputes"],
    ["returns", "/admin/returns"],
    ["tickets", "/admin/tickets"],
    ["treasury", "/admin/finance?section=treasury"],
  ] as const) {
    await step(page, ACTOR, `${name}-operations`, async () => {
      await page.goto(path, { waitUntil: "domcontentloaded", timeout: 60_000 });
      await waitForContent(page, ['table tbody tr', '[role="row"]', "article"], 35_000);
    });
    log.record(name, "rows", (await countRows(page)) > 0 ? "ok" : "not-found", `${await countRows(page)} rows`);
  }

  // ── Governance / audit ────────────────────────────────────────────────
  await step(page, ACTOR, "audit-logs", async () => {
    await page.goto("/admin/audit-logs", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await waitForContent(page, ['table tbody tr', '[role="row"]'], 40_000);
  });
  log.record("audit", "audit rows", (await countRows(page)) > 0 ? "ok" : "not-found", `${await countRows(page)} rows`);

  const diag = await collectDiagnostics(page);
  log.write(ACTOR, [
    `User rows: ${userRows}`,
    `Final URL: ${diag.url}`,
    `Console errors: ${diag.consoleErrors.length}`,
    `Failed requests: ${diag.failedRequests.length}`,
    `4xx/5xx: ${diag.httpErrors.length}`,
    ...diag.httpErrors.slice(0, 12).map((e) => `- ${e}`),
  ]);
});