/**
 * Logistics-partner journey — the physical fulfilment chain.
 *
 * Covers the operational flow a logistics partner actually performs: see the
 * shipment manifest, open a shipment, scan/verify parcels, advance delivery
 * status, and handle exceptions. Also captures the rate-card surfaces that drive
 * shipping quotes.
 */
import { test } from "@playwright/test";
import { bootstrapLogisticsSession } from "../../src/auth";
import { step, settle, collectDiagnostics } from "../../src/evidence";
import { JourneyLog, clickAny, fillAny, countRows, waitForContent } from "../../src/journey";

const ACTOR = "logistics";
const SEED = process.env.SEED_LOGISTICS_PASSWORD || "E2eLogistics#2026";

test.describe.configure({ timeout: 1_500_000 });

test("logistics: fulfilment and delivery journey", async ({ page }) => {
  const log = new JourneyLog();
  const seeded = await bootstrapLogisticsSession(page);
  log.record("session", seeded ? "api bootstrap" : "api bootstrap failed", seeded ? "ok" : "error");
  if (!seeded) {
    await page.goto("/login", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await fillAny(page, [{ role: "textbox" }, 'input[type="email"]'], "logistics@zozi.com", log, "login");
    await fillAny(page, ['input[type="password"]'], SEED, log, "login");
    await clickAny(page, [{ role: "button", name: /sign in|log in/i }], log, "login");
    await settle(page);
  }

  await step(page, ACTOR, "dashboard", async () => {
    await page.goto("/logistics-partner/dashboard", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await settle(page);
  });
  log.record("dashboard", "kpi cards", "ok", `${await countRows(page)} rows`);

  // Shipment manifest — the core operational list.
  await step(page, ACTOR, "shipments-list", async () => {
    await page.goto("/logistics-partner/shipments", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await waitForContent(page, ['table tbody tr', '[role="row"]', "article"], 45_000);
  });
  const shipments = await countRows(page);
  log.record("shipments", "manifest rows", shipments > 0 ? "ok" : "not-found", `${shipments} rows`);

  await step(page, ACTOR, "shipment-detail", async () => {
    const first = await page
      .locator('a[href*="/shipments/"], a[href*="/logistics-partner/orders/"], [role="row"], table tbody tr')
      .first();
    if (await first.isVisible({ timeout: 6_000 }).catch(() => false)) {
      await first.click({ timeout: 8_000 }).catch(() => {});
      log.record("shipment-detail", "open shipment", "ok", page.url());
    } else {
      log.record("shipment-detail", "open shipment", "not-found");
    }
  });

  // Parcel verification — scan or key in a tracking id.
  // The route is /logistics-partner/scan (there is no parcel-verification page).
  await step(page, ACTOR, "parcel-verification", async () => {
    await page.goto("/logistics-partner/scan", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });
  await step(page, ACTOR, "parcel-scan-input", async () => {
    await fillAny(
      page,
      ['input[name*="tracking" i]', 'input[name*="parcel" i]', 'input[placeholder*="tracking" i]', 'input[placeholder*="scan" i]'],
      "ZVJ-E2E-0001",
      log,
      "parcel",
    );
  });
  await step(page, ACTOR, "parcel-verify-action", () =>
    clickAny(page, [{ role: "button", name: /verify|scan|lookup|check/i }, { text: /verify|scan/i }], log, "parcel"),
  );

  // Delivery status transitions — the business logic of fulfilment.
  for (const [name, label] of [
    ["mark-picked-up", /mark.*(picked|collected)|pick up|collect/i],
    ["mark-in-transit", /in transit|dispatch|out for delivery/i],
    ["mark-delivered", /mark.*delivered|complete delivery|confirm delivery/i],
  ] as const) {
    await step(page, ACTOR, name, () => clickAny(page, [{ role: "button", name: label }, { text: label }], log, name));
  }

  // Exceptions and proof of delivery.
  await step(page, ACTOR, "proof-of-delivery", () =>
    clickAny(page, [{ role: "button", name: /proof of delivery|pod|signature|upload.*proof/i }, { text: /proof of delivery|pod/i }], log, "pod"),
  );

  // Rate card + country switching (drives shipping quotes).
  await step(page, ACTOR, "pricing-and-countries", async () => {
    await page.goto("/logistics-partner/profile", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  await step(page, ACTOR, "barcode-scan", async () => {
    await page.goto("/barcode-scan", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  const diag = await collectDiagnostics(page);
  log.write(ACTOR, [
    `Shipment rows: ${shipments}`,
    `Final URL: ${diag.url}`,
    `Console errors: ${diag.consoleErrors.length}`,
    `Failed requests: ${diag.failedRequests.length}`,
    `4xx/5xx: ${diag.httpErrors.length}`,
    ...diag.httpErrors.slice(0, 8).map((e) => `- ${e}`),
  ]);
});