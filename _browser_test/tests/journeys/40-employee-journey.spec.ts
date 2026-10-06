/**
 * Employee journey — the HR operations an employee role performs.
 *
 * Note: employees are seeded per country (<cc>.manager@zozi.com etc.) and share
 * the DevSeed123! password. There is no employee@zozi.com account; the root .env
 * even records SEED_EMPLOYEE_PASSWORD=employee123, which matches nothing.
 */
import { test } from "@playwright/test";
import { bootstrapEmployeeSession } from "../../src/auth";
import { step, settle, collectDiagnostics } from "../../src/evidence";
import { JourneyLog, clickAny, fillAny, countRows, waitForContent } from "../../src/journey";

const ACTOR = "employee";
const SEED = process.env.SEED_EMPLOYEE_PASSWORD || "DevSeed123!";
const EMAIL = process.env.SEED_EMPLOYEE_EMAIL || "ae.manager@zozi.com";

test.describe.configure({ timeout: 1_500_000 });

test("employee: HR operations journey", async ({ page }) => {
  const log = new JourneyLog();
  const seeded = await bootstrapEmployeeSession(page);
  log.record("session", seeded ? `api bootstrap (${EMAIL})` : "api bootstrap failed", seeded ? "ok" : "error");
  if (!seeded) {
    await page.goto("/employee/login", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await fillAny(page, [{ role: "textbox" }, 'input[type="email"]'], EMAIL, log, "login");
    await fillAny(page, ['input[type="password"]'], SEED, log, "login");
    await clickAny(page, [{ role: "button", name: /sign in|log in/i }], log, "login");
    await settle(page);
  }

  await step(page, ACTOR, "dashboard", async () => {
    await page.goto("/employee/dashboard", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await settle(page);
  });
  log.record("dashboard", "kpi cards", "ok", `${await countRows(page)} rows`);

  // Attendance — clock in/out is the daily business action.
  await step(page, ACTOR, "attendance", async () => {
    await page.goto("/employee/attendance", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await waitForContent(page, ['table tbody tr', '[role="row"]'], 40_000);
  });
  log.record("attendance", "records", (await countRows(page)) > 0 ? "ok" : "not-found", `${await countRows(page)} rows`);

  await step(page, ACTOR, "attendance-clock-action", () =>
    clickAny(page, [{ role: "button", name: /clock (in|out)|check (in|out)|punch/i }, { text: /clock (in|out)|check (in|out)/i }], log, "attendance"),
  );

  // Leave management — request + approval queue.
  await step(page, ACTOR, "leaves", async () => {
    await page.goto("/employee/leaves", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });
  await step(page, ACTOR, "leave-request-form", () =>
    clickAny(page, [{ role: "button", name: /request leave|new leave|apply for leave|\+.*leave/i }, { text: /request leave|apply for leave/i }], log, "leaves"),
  );
  await step(page, ACTOR, "leave-approve-action", () =>
    clickAny(page, [{ role: "button", name: /approve|reject|review/i }, { text: /approve|reject/i }], log, "leaves"),
  );

  // Performance and goals.
  await step(page, ACTOR, "performance", async () => {
    await page.goto("/employee/performance", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  // Payroll — sensitive, must be permission-gated.
  await step(page, ACTOR, "payroll", async () => {
    await page.goto("/employee/payroll", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  await step(page, ACTOR, "training", async () => {
    await page.goto("/employee/training", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  await step(page, ACTOR, "schedule", async () => {
    await page.goto("/employee/schedule", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  await step(page, ACTOR, "documents", async () => {
    await page.goto("/employee/documents", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  await step(page, ACTOR, "workspace-tasks", async () => {
    await page.goto("/employee/workspace/tasks", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });
  log.record("workspace", "task rows", (await countRows(page)) > 0 ? "ok" : "not-found", `${await countRows(page)} rows`);

  await step(page, ACTOR, "profile", async () => {
    await page.goto("/employee/profile", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  // The admin-facing HR dashboard this role may also reach.
  await step(page, ACTOR, "admin-hr-dashboard", async () => {
    await page.goto("/admin/hr", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await settle(page, { budgetMs: 35_000 });
  });
  log.record("admin-hr", "stat cards", (await countRows(page)) > 0 ? "ok" : "not-found", `${await countRows(page)} rows`);

  const diag = await collectDiagnostics(page);
  log.write(ACTOR, [
    `Employee account: ${EMAIL}`,
    `Final URL: ${diag.url}`,
    `Console errors: ${diag.consoleErrors.length}`,
    `Failed requests: ${diag.failedRequests.length}`,
    `4xx/5xx: ${diag.httpErrors.length}`,
    ...diag.httpErrors.slice(0, 8).map((e) => `- ${e}`),
  ]);
});