/**
 * Route walkthrough Ã¢â‚¬â€ evidence collection, not assertion.
 *
 * Walks every page route in frontend/web_app/src/app, captures a screenshot and a
 * diagnostics record for each, and writes an actor-grouped report. This is how the
 * routes that no feature spec touches get seen at all: 79 of 155 page routes had no
 * mention anywhere in the suite before this spec existed.
 *
 * The route list is derived from the filesystem at run time, so a new page in the
 * app is picked up automatically instead of silently staying invisible.
 *
 * Not a pass/fail gate on purpose. A 404 or a console error is recorded as
 * evidence for review; it does not redden the run. Gate regressions live in the
 * feature specs.
 */
import fs from "node:fs";
import path from "node:path";
import { test, expect, type Page } from "@playwright/test";
import {
  bootstrapAdminSessionViaApi,
  bootstrapSupplierSession,
  bootstrapLogisticsSession,
  bootstrapCustomerSession,
  bootstrapEmployeeSession,
  waitForSessionFlag,
  submitCredentialForm,
} from "../src/auth";
import { step, collectDiagnostics, mockExternals, writeActorReport, RUN_ID } from "../src/evidence";

const REPO_ROOT = path.resolve(__dirname, "../..");
const APP_DIR = path.join(REPO_ROOT, "frontend/web_app/src/app");

/** Verified against the live API on 2026-10-03. */
const SEED = {
  admin: process.env.SEED_ADMIN_PASSWORD || "E2eAdmin#2026",
  supplier: process.env.SEED_SUPPLIER_PASSWORD || "E2eSupplier#2026",
  logistics: process.env.SEED_LOGISTICS_PASSWORD || "E2eLogistics#2026",
  customer: process.env.SEED_CUSTOMER_PASSWORD || "E2eCustomer#2026",
  // Employees are per-country and share the DevSeed123! password; there is no
  // employee@zozi.com account.
  employee: process.env.SEED_EMPLOYEE_PASSWORD || "DevSeed123!",
};

/** Plausible ids for dynamic segments, so /products/[id] is actually visited. */
const DYNAMIC_SAMPLES: Record<string, string> = {
  id: "1",
  code: "SA",
  slug: "demo",
  room: "demo-room",
  token: "demo-token",
};

type Actor = "public" | "customer" | "supplier" | "logistics" | "employee" | "admin";

function classify(route: string): Actor {
  if (/^\/(admin)(?:\/|$)/.test(route)) return "admin";
  if (/^\/(supplier)(?:\/|$)/.test(route)) return "supplier";
  if (/^\/(logistics-partner)(?:\/|$)/.test(route)) return "logistics";
  if (/^\/(employee)(?:\/|$)/.test(route)) return "employee";
  if (/^\/(cart|checkout|orders|wishlist|profile|returns|tickets|tracking|notifications|offers|profile)/.test(route))
    return "customer";
  return "public";
}

function discoverRoutes(): string[] {
  const out: string[] = [];
  const walk = (dir: string, prefix: string) => {
    let entries: fs.Dirent[];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const e of entries) {
      if (e.isDirectory()) {
        walk(path.join(dir, e.name), `${prefix}/${e.name}`);
      } else if (e.name === "page.tsx") {
        const clean = prefix
          .split("/")
          .filter((s) => s && !(s.startsWith("(") && s.endsWith(")")))
          .map((s) =>
            s.startsWith("[...") ? "*" : s.startsWith("[") ? DYNAMIC_SAMPLES[s.slice(1, -1)] ?? "1" : s,
          )
          .join("/");
        out.push(`/${clean}`.replace(/\/+$/, "") || "/");
      }
    }
  };
  walk(APP_DIR, "");
  return [...new Set(out)].sort();
}

const ROUTES = discoverRoutes();
const BY_ACTOR = ROUTES.reduce<Record<string, string[]>>((acc, r) => {
  const a = classify(r);
  (acc[a] ??= []).push(r);
  return acc;
}, {});

/**
 * Best-effort session. Never throws.
 *
 * If bootstrap fails Ã¢â‚¬â€ bad credentials, a 500 from the auth endpoint, a backend
 * that is down Ã¢â‚¬â€ we still walk the routes anonymously. A login failure is itself
 * evidence worth capturing, and it must not abort the walk.
 */
async function ensureSession(page: Page, actor: Actor): Promise<string> {
  const creds: Record<string, [string, string]> = {
    admin: ["admin@zozi.com", SEED.admin],
    supplier: ["supplier@zozi.com", SEED.supplier],
    logistics: ["logistics@zozi.com", SEED.logistics],
    customer: ["customer@zozi.com", SEED.customer],
    employee: [process.env.SEED_EMPLOYEE_EMAIL || "ae.manager@zozi.com", SEED.employee],
    public: ["", ""],
  };
  const [user, pass] = creds[actor];
  if (!user) return "anonymous";

  try {
    const seeded =
      actor === "admin"
        ? await bootstrapAdminSessionViaApi(page)
        : actor === "employee"
          ? await bootstrapEmployeeSession(page)
          : actor === "supplier"
            ? await bootstrapSupplierSession(page)
            : actor === "logistics"
              ? await bootstrapLogisticsSession(page)
              : await bootstrapCustomerSession(page);
    if (seeded) return "api";
  } catch {
    // fall through to the form
  }

  try {
    const loginPath =
      actor === "admin" ? "/admin/login" : actor === "employee" ? "/employee/login" : "/login";
    await page.goto(loginPath, { waitUntil: "domcontentloaded", timeout: 60_000 });
    await submitCredentialForm(page, user, pass);
    await waitForSessionFlag(page, 30_000);
    return "ui-form";
  } catch (error) {
    console.warn(
      `[route-walk] ${actor}: session bootstrap failed (${String(error).split("\n")[0]}); ` +
        "continuing anonymously so the screens are still captured.",
    );
    return "anonymous (auth unavailable)";
  }
}

test.describe.configure({ timeout: 900_000 });

test("route inventory is discovered from the app tree", async () => {
  // Guard against silently walking nothing if the path assumption breaks.
  expect(ROUTES.length, `no routes discovered from ${APP_DIR}`).toBeGreaterThan(50);
});

for (const [actor, routes] of Object.entries(BY_ACTOR).sort()) {
  test(`${actor}: walk ${routes.length} routes and record evidence`, async ({ page }) => {
    // Dev-mode Next.js compiles each route on first hit, so the budget has to
    // scale with the number of routes rather than being a fixed 15 minutes.
    test.setTimeout(Math.max(900_000, routes.length * 35_000));
    await mockExternals(page);
    const how = await ensureSession(page, actor as Actor);

    const report: string[] = [
      `Run: ${RUN_ID}`,
      `Session: ${how}`,
      `Routes: ${routes.length}`,
      "",
      "| route | http | overflow | console err | failed req | 4xx/5xx |",
      "|---|---|---|---|---|---|",
    ];

    for (const route of routes) {
      let diag;
      try {
        let status = 0;
        await step(page, actor, route, async () => {
          const response = await page.goto(route, {
            waitUntil: "domcontentloaded",
            timeout: 60_000,
          });
          status = response?.status() ?? 0;
          await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => {});
        });
        diag = await collectDiagnostics(page);
        report.push(
          `| \`${route}\` | ${status} | ${diag.overflowPx}px | ${diag.consoleErrors.length} | ${diag.failedRequests.length} | ${diag.httpErrors.length} |`,
        );
        for (const e of diag.httpErrors.slice(0, 4)) report.push(`  - http: ${e}`);
        for (const e of diag.consoleErrors.slice(0, 4)) report.push(`  - console: ${e}`);
      } catch (error) {
        report.push(`| \`${route}\` | ERROR | Ã¢â‚¬â€ | Ã¢â‚¬â€ | Ã¢â‚¬â€ | Ã¢â‚¬â€ |`);
        report.push(`  - walk failed: ${String(error).slice(0, 300)}`);
      }
    }

    writeActorReport(actor, report);
  });
}
