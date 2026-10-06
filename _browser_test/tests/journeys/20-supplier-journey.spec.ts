/**
 * Supplier journey — onboarding, catalogue operations, order fulfilment and payouts.
 *
 * Exercises the supplier-side business logic against the live backend: product
 * creation inputs, inventory/listing views, order state transitions and the
 * earnings/payout surfaces. Every interaction is recorded in journeys.md and
 * captured as before/after evidence.
 */
import { test } from "@playwright/test";
import { bootstrapSupplierSession } from "../../src/auth";
import { step, settle, collectDiagnostics } from "../../src/evidence";
import {
  JourneyLog,
  clickAny,
  fillAny,
  countRows,
  waitForContent,
  ADD_TO_CART,
  type Candidate,
} from "../../src/journey";

const ACTOR = "supplier";
const SEED = process.env.SEED_SUPPLIER_PASSWORD || "E2eSupplier#2026";

test.describe.configure({ timeout: 1_500_000 });

export const TAB: Candidate[] = [
  { role: "tab", name: /./ },
  '[role="tab"]',
  'button:has-text("Tab")',
];

test("supplier: catalogue, orders and payouts journey", async ({ page }) => {
  const log = new JourneyLog();
  const seeded = await bootstrapSupplierSession(page);
  log.record("session", seeded ? "api bootstrap" : "api bootstrap failed", seeded ? "ok" : "error");
  if (!seeded) {
    await page.goto("/login", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await fillAny(page, [{ role: "textbox" }, 'input[type="email"]'], "supplier@zozi.com", log, "login");
    await fillAny(page, ['input[type="password"]'], SEED, log, "login");
    await clickAny(page, [{ role: "button", name: /sign in|log in/i }], log, "login");
    await settle(page);
  }

  // ── Dashboard ─────────────────────────────────────────────────────────
  await step(page, ACTOR, "dashboard", async () => {
    await page.goto("/supplier/dashboard", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await settle(page);
  });
  log.record("dashboard", "kpi cards", "ok", `${await countRows(page)} rows`);

  // ── Catalogue: list, add, edit ────────────────────────────────────────
  await step(page, ACTOR, "catalog-list", async () => {
    await page.goto("/supplier/products", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await waitForContent(page, ['table tbody tr', '[role="row"]', "article"], 45_000);
  });
  const catalogRows = await countRows(page);
  log.record("catalog", "my products", catalogRows > 0 ? "ok" : "not-found", `${catalogRows} rows`);

  await step(page, ACTOR, "catalog-add-product-form", () =>
    clickAny(
      page,
      [
        { role: "button", name: /add product|new product|create product|\+\s*add/i },
        { text: /add product|new product/i },
        '[data-testid="add-product"]',
      ],
      log,
      "catalog-add",
    ),
  );

  await step(page, ACTOR, "catalog-product-fields", async () => {
    await page.waitForLoadState("domcontentloaded", { timeout: 30_000 }).catch(() => {});
    const filled = [
      await fillAny(page, ['input[name*="name" i]', 'input[placeholder*="name" i]'], "E2E Journey Product", log, "product-form"),
      await fillAny(page, ['input[name*="sku" i]', 'input[placeholder*="sku" i]'], `E2E-${Date.now()}`, log, "product-form"),
      await fillAny(page, ['input[name*="price" i]', 'input[type="number"]'], "149.000", log, "product-form"),
      await fillAny(page, ['input[name*="stock" i]'], "25", log, "product-form"),
      await fillAny(page, ['textarea[name*="description" i]', 'textarea'], "Created by the automated browser journey to verify the supplier product workflow end to end.", log, "product-form"),
    ];
    log.record("product-form", "fields filled", filled.filter(Boolean).length > 0 ? "ok" : "not-found", `${filled.filter(Boolean).length}/5`);
  });

  await step(page, ACTOR, "catalog-submit-product", () =>
    clickAny(
      page,
      [
        { role: "button", name: /^(save|create|publish|submit)/i },
        { text: /^(save|create|publish)/i },
        { role: "button", name: /save (product|draft)/i },
      ],
      log,
      "catalog-submit",
    ),
  );

  // ── Orders and fulfilment ─────────────────────────────────────────────
  await step(page, ACTOR, "orders-list", async () => {
    await page.goto("/supplier/orders", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await waitForContent(page, ['table tbody tr', '[role="row"]'], 45_000);
  });
  const orderRows = await countRows(page);
  log.record("orders", "assigned orders", orderRows > 0 ? "ok" : "not-found", `${orderRows} rows`);

  await step(page, ACTOR, "order-detail-and-fulfil", async () => {
    const first = await page.locator('a[href*="/supplier/orders/"], [role="row"], table tbody tr').first();
    if (await first.isVisible({ timeout: 6_000 }).catch(() => false)) {
      await first.click({ timeout: 8_000 }).catch(() => {});
      log.record("order-detail-and-fulfil", "open order", "ok", page.url());
    } else {
      log.record("order-detail-and-fulfil", "open order", "not-found");
    }
  });

  await step(page, ACTOR, "advance-order-status", () =>
    clickAny(
      page,
      [
        { role: "button", name: /mark (as )?(shipped|ready|packed|dispatched)/i },
        { role: "button", name: /confirm|advance|update status/i },
        { text: /mark as shipped|ship order|dispatch/i },
      ],
      log,
      "advance-status",
    ),
  );

  // ── Bulk operations ───────────────────────────────────────────────────
  await step(page, ACTOR, "bulk-upload", async () => {
    await page.goto("/supplier/batch-upload", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  // ── Money: earnings, commissions, payouts ─────────────────────────────
  for (const [name, path] of [
    ["earnings", "/supplier/commission"],
    ["payouts", "/supplier/invoices"],
    ["analytics", "/supplier/analytics"],
  ] as const) {
    await step(page, ACTOR, `${name}-view`, async () => {
      await page.goto(path, { waitUntil: "domcontentloaded", timeout: 60_000 });
      await settle(page, { budgetMs: 35_000 });
    });
    log.record(name, "surface", "ok", `${await countRows(page)} rows @ ${path}`);
  }

  // ── Trust & compliance ────────────────────────────────────────────────
  await step(page, ACTOR, "kyc-status", async () => {
    await page.goto("/supplier/kyc", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });
  await step(page, ACTOR, "credibility-score", async () => {
    await page.goto("/supplier/credibility", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  const diag = await collectDiagnostics(page);
  log.write(ACTOR, [
    `Catalogue rows: ${catalogRows}`,
    `Order rows: ${orderRows}`,
    `Final URL: ${diag.url}`,
    `Console errors: ${diag.consoleErrors.length}`,
    `Failed requests: ${diag.failedRequests.length}`,
    `4xx/5xx: ${diag.httpErrors.length}`,
    ...diag.httpErrors.slice(0, 8).map((e) => `- ${e}`),
  ]);
});