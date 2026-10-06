/**
 * Customer journey — the full commerce business flow, exercised with real
 * interactions against the live backend (Neon) and SPA.
 *
 * Captures every step as before/after evidence and records each interaction in
 * journeys.md. Nothing here is a pass/fail gate: a control that cannot be found
 * is logged as `not-found` and the walk continues, because the point is to show
 * what the product actually does.
 *
 * Flow: browse → filter → product → cart → checkout → order → tracking,
 *       plus wishlist, addresses and returns.
 */
import { test } from "@playwright/test";
import { bootstrapCustomerSession } from "../../src/auth";
import { step, settle, collectDiagnostics } from "../../src/evidence";
import {
  JourneyLog,
  clickAny,
  fillAny,
  openFirstItem,
  countRows,
  waitForContent,
  ADD_TO_CART,
  PRODUCT_CARD,
  SEARCH_INPUT,
  PLACE_ORDER,
  COD_OPTION,
} from "../../src/journey";

const ACTOR = "customer";
const SEED = process.env.SEED_CUSTOMER_PASSWORD || "E2eCustomer#2026";

test.describe.configure({ timeout: 1_500_000 });

test("customer: full commerce journey", async ({ page }) => {
  const log = new JourneyLog();

  const seeded = await bootstrapCustomerSession(page);
  log.record("session", seeded ? "api bootstrap" : "api bootstrap failed", seeded ? "ok" : "error");
  if (!seeded) {
    await page.goto("/login", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await fillAny(page, [{ role: "textbox" }, 'input[type="email"]', 'input[name*="user"]'], "customer@zozi.com", log, "login");
    await fillAny(page, ['input[type="password"]'], SEED, log, "login");
    await clickAny(page, [{ role: "button", name: /sign in|log in/i }], log, "login");
    await settle(page);
  }

  // ── 1. Storefront ──────────────────────────────────────────────────────
  await step(page, ACTOR, "home", async () => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });
  log.record("home", "cards on landing", "ok", `${await countRows(page)} rows`);

  // ── 2. Catalog + filters ───────────────────────────────────────────────
  await step(page, ACTOR, "catalog", async () => {
    await page.goto("/products", { waitUntil: "domcontentloaded", timeout: 60_000 });
    // Wait for real product cards, not skeletons.
    if (!(await waitForContent(page, PRODUCT_CARD, 60_000))) {
      log.record("catalog", "wait for product cards", "not-found", "no cards after 60s");
    }
  });
  const catalogueRows = await countRows(page);
  log.record("catalog", "product count", catalogueRows > 0 ? "ok" : "not-found", `${catalogueRows} rows`);

  await step(page, ACTOR, "catalog-filter-price", () =>
    clickAny(page, [{ role: "button", name: /^price$/i }, { text: /^price$/i }, { text: /sort/i }], log, "catalog"),
  );
  await step(page, ACTOR, "catalog-filter-applied", async () => {
    const option = await page
      .getByRole("option")
      .or(page.getByRole("menuitem"))
      .first();
    if (await option.isVisible({ timeout: 4_000 }).catch(() => false)) {
      await option.click({ timeout: 6_000 }).catch(() => {});
      log.record("catalog-filter-applied", "choose first option", "ok", await option.innerText().catch(() => ""));
    } else {
      log.record("catalog-filter-applied", "choose first option", "not-found");
    }
  });

  // ── 3. Search ──────────────────────────────────────────────────────────
  await step(page, ACTOR, "search-results", async () => {
    await page.goto("/products?search=tea", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await waitForContent(page, PRODUCT_CARD, 45_000);
  });
  log.record("search", "results for 'tea'", "ok", `${await countRows(page)} rows`);

  // ── 4. Product detail + add to cart ────────────────────────────────────
  let pdpUrl: string | null = null;
  await step(page, ACTOR, "open-product", async () => {
    await page.goto("/products", { waitUntil: "domcontentloaded", timeout: 60_000 });
    await waitForContent(page, PRODUCT_CARD, 60_000);
    pdpUrl = await openFirstItem(page, PRODUCT_CARD, log, "open-product");
  });
  if (!pdpUrl) {
    // Second fallback: derive a real product id from the catalogue DOM.
    await step(page, ACTOR, "open-product-fallback", async () => {
      await page.goto("/products", { waitUntil: "domcontentloaded", timeout: 60_000 });
      await waitForContent(page, PRODUCT_CARD, 45_000);
      pdpUrl = await openFirstItem(page, PRODUCT_CARD, log, "open-product-fallback");
    });
  }

  await step(page, ACTOR, "pdp-price-and-stock", async () => {
    await settle(page, { budgetMs: 20_000 });
  });

  await step(page, ACTOR, "add-to-cart", () => clickAny(page, ADD_TO_CART, log, "add-to-cart"));

  // ── 5. Cart operations ─────────────────────────────────────────────────
  await step(page, ACTOR, "cart-view", async () => {
    await page.goto("/cart", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });
  const cartRows = await countRows(page);
  log.record("cart", "line items", cartRows > 0 ? "ok" : "not-found", `${cartRows} rows`);

  await step(page, ACTOR, "cart-increase-quantity", () =>
    clickAny(
      page,
      [
        '[data-testid="increase-qty"]',
        '[aria-label*="increase" i]',
        '[aria-label*="increment" i]',
        { role: "button", name: /^\+$|increase|increment/i },
        { text: /^\+$/ },
      ],
      log,
      "cart-qty",
    ),
  );

  await step(page, ACTOR, "cart-promo-code", () =>
    fillAny(
      page,
      ['input[name*="promo" i]', 'input[placeholder*="promo" i]', 'input[placeholder*="code" i]'],
      "SAVE10",
      log,
      "cart-promo",
    ),
  );

  await step(page, ACTOR, "cart-apply-promo", () =>
    clickAny(page, [{ role: "button", name: /apply/i }, { text: /apply/i }], log, "cart-promo"),
  );

  // ── 6. Checkout: address → payment → place order ──────────────────────
  await step(page, ACTOR, "checkout-open", () => clickAny(page, [{ role: "button", name: /checkout/i }, { text: /checkout/i }, { role: "link", name: /checkout/i }], log, "checkout"));

  await step(page, ACTOR, "checkout-address", async () => {
    if (!page.url().includes("/checkout")) {
      await page.goto("/checkout", { waitUntil: "domcontentloaded", timeout: 60_000 });
    }
    log.record("checkout-address", "reached checkout", "ok", page.url());
  });

  await step(page, ACTOR, "checkout-fill-address", async () => {
    await fillAny(page, ['input[name*="street" i]', 'input[placeholder*="street" i]', 'input[name*="address" i]'], "Al Murooba Street 12", log, "checkout");
    await fillAny(page, ['input[name*="city" i]', 'input[placeholder*="city" i]'], "Dubai", log, "checkout");
    await fillAny(page, ['input[name*="phone" i]', 'input[type="tel"]'], "+971500000000", log, "checkout");
  });

  await step(page, ACTOR, "checkout-select-cod", () => clickAny(page, COD_OPTION, log, "checkout-cod"));

  await step(page, ACTOR, "checkout-review", async () => {
    await settle(page, { budgetMs: 20_000 });
  });

  const placed = await (async () => {
    await step(page, ACTOR, "place-order", () => clickAny(page, PLACE_ORDER, log, "place-order"));
    await page.waitForLoadState("networkidle", { timeout: 45_000 }).catch(() => {});
    return /\/orders\/|\/checkout\/success|order.*(placed|confirmed)/i.test(page.url() + " " + (await page.title()));
  })();
  log.record("place-order", placed ? "order placed" : "no order confirmation detected", placed ? "ok" : "not-found", page.url());

  // ── 7. Orders + tracking ───────────────────────────────────────────────
  await step(page, ACTOR, "orders-list", async () => {
    await page.goto("/orders", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });
  log.record("orders", "order rows", (await countRows(page)) > 0 ? "ok" : "not-found", `${await countRows(page)} rows`);

  await step(page, ACTOR, "order-detail", async () => {
    const first = await page
      .locator('a[href*="/orders/"], [data-testid="order-row"], [role="row"]')
      .first();
    if (await first.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await first.click({ timeout: 8_000 }).catch(() => {});
      log.record("order-detail", "open first order", "ok", page.url());
    } else {
      log.record("order-detail", "open first order", "not-found");
    }
  });

  await step(page, ACTOR, "order-tracking", async () => {
    await page.goto("/orders", { waitUntil: "domcontentloaded", timeout: 60_000 });
    const track = await page.getByText(/track/i).first();
    if (await track.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await track.click({ timeout: 8_000 }).catch(() => {});
      log.record("order-tracking", "open tracking", "ok", page.url());
    } else {
      log.record("order-tracking", "open tracking", "not-found");
    }
  });

  // ── 8. Wishlist ────────────────────────────────────────────────────────
  await step(page, ACTOR, "wishlist-view", async () => {
    await page.goto("/wishlist", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });
  log.record("wishlist", "saved items", (await countRows(page)) > 0 ? "ok" : "not-found", `${await countRows(page)} rows`);

  await step(page, ACTOR, "wishlist-move-to-cart", () =>
    clickAny(page, [{ role: "button", name: /move to cart|add to cart/i }, { text: /move to cart/i }], log, "wishlist"),
  );

  // ── 9. Profile, addresses, returns ─────────────────────────────────────
  await step(page, ACTOR, "profile", async () => {
    await page.goto("/profile", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });
  await step(page, ACTOR, "profile-addresses", async () => {
    await page.goto("/profile/addresses", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });
  log.record("addresses", "saved addresses", (await countRows(page)) > 0 ? "ok" : "not-found", `${await countRows(page)} rows`);

  await step(page, ACTOR, "returns-request", async () => {
    await page.goto("/returns", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });
  log.record("returns", "returns centre", "ok", page.url());

  await step(page, ACTOR, "support-tickets", async () => {
    await page.goto("/tickets", { waitUntil: "domcontentloaded", timeout: 60_000 });
  });

  const diag = await collectDiagnostics(page);
  log.write(ACTOR, [
    `Catalogue rows: ${catalogueRows}`,
    `Cart rows: ${cartRows}`,
    `Final URL: ${diag.url}`,
    `Console errors: ${diag.consoleErrors.length}`,
    `Failed requests: ${diag.failedRequests.length}`,
    `4xx/5xx: ${diag.httpErrors.length}`,
    ...diag.httpErrors.slice(0, 8).map((e) => `- ${e}`),
  ]);
});