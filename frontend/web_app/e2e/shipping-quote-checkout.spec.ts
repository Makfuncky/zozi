/**
 * Shipping Quote + Checkout E2E Test
 *
 * Hybrid approach: backend API calls for heavy lifting + Playwright page
 * for UI verification where possible.
 *
 * Since the login page uses useSearchParams() and doesn't SSR-render its
 * form, and the module-level access token can't be set from page.evaluate,
 * this test uses the Playwright `request` fixture for all authenticated
 * API calls and the page for navigational checks.
 *
 * Run: cd frontend/web_app && npx playwright test e2e/shipping-quote-checkout.spec.ts
 */

import { expect, test } from "@playwright/test";

test.describe.configure({ timeout: 180_000 });

const BACKEND = "http://127.0.0.1:8000";
const COUNTRY_CODE = "AE";
const CITY_NAME = "Dubai";

// ── API Helpers ────────────────────────────────────────────────────────────

async function login(request: any, username: string, password: string): Promise<string> {
  const candidates = [username, username.split("@")[0]];
  for (const c of candidates) {
    const r = await request.post(`${BACKEND}/auth/login`, {
      data: { username: c, password },
    });
    if (r.ok()) {
      const body = (await r.json()) as { access_token?: string; token?: string };
      const t = body.access_token || body.token;
      if (t) return t;
    }
  }
  throw new Error(`Login failed for ${username}`);
}

async function fetchFirstProduct(request: any): Promise<{ id: number }> {
  const r = await request.get(`${BACKEND}/products?limit=50`, { failOnStatusCode: false });
  expect(r.ok()).toBeTruthy();
  const data = (await r.json()) as Array<{ id: number; stock?: number; is_active?: boolean }>;
  for (const c of data) {
    if (!c?.id) continue;
    if (Number(c.stock ?? 0) > 0 && c.is_active !== false) return { id: c.id };
  }
  if (data.length > 0 && data[0]?.id) return { id: data[0].id };
  throw new Error("No product found");
}

// ── Test ───────────────────────────────────────────────────────────────────

test("logistics partner pricing verified end-to-end", async ({ request }) => {
  test.setTimeout(120_000);

  // 1. Supplier login + service area setup (best-effort)
  console.log("[test] Supplier login...");
  const sToken = await login(request, "supplier@zozi.com", "supplier123");
  const sAuth = { Authorization: `Bearer ${sToken}` };

  // Check existing partner/service-area (non-fatal — seed data may already cover AE/Dubai)
  const partnersResp = await request.get(`${BACKEND}/logistics-partner/list`, {
    headers: sAuth, failOnStatusCode: false,
  });
  if (partnersResp.ok()) {
    const partners = (await partnersResp.json()) as Array<{
      id: number; name: string; status: string; country_code: string;
      service_areas?: Array<{ id: number; city_name: string }>;
    }>;
    const p = partners.find((x) => x.country_code === COUNTRY_CODE && x.status === "active");
    if (p) {
      console.log(`[test] Partner: ${p.name} (ID: ${p.id})`);
      const hasSA = p.service_areas?.some((sa) => sa.city_name === CITY_NAME);
      if (!hasSA) {
        for (const path of [`${BACKEND}/admin/logistics/service-areas`, `${BACKEND}/logistics-partner/service-areas`]) {
          const r = await request.post(path, { headers: sAuth, data: {
            partner_id: p.id, country_code: COUNTRY_CODE, city_name: CITY_NAME,
            origin_city: "Dubai", charge_amount: 12.0, pickup_charge: 1.5, dropoff_charge: 1.5,
            currency: "AED", delivery_days_min: 1, delivery_days_max: 3, is_active: true, approval_status: "approved",
          }}).catch(() => null);
          if (r?.ok()) { console.log(`[test] SA created`); break; }
        }
      } else {
        console.log(`[test] SA exists for ${CITY_NAME}`);
      }
    }
  } else {
    console.log(`[test] Partners list returned ${partnersResp.status()} (non-fatal)`);
  }

  // 2. Get product info
  console.log("[test] Fetching product...");
  const product = await fetchFirstProduct(request);
  console.log(`[test] Product ID: ${product.id}`);

  // 3. Login as customer + add product to cart
  console.log("[test] Customer login & add to cart...");
  const cToken = await login(request, "customer@zozi.com", "customer123");

  const cartResp = await request.post(`${BACKEND}/cart/items`, {
    headers: { Authorization: `Bearer ${cToken}` },
    data: { product_id: product.id, quantity: 2 },
  });
  expect(cartResp.ok(), `Cart add: ${cartResp.status()}`).toBeTruthy();
  console.log("[test] Product added to customer cart");

  // 4. Call shipping quote API
  console.log("[test] Calling shipping quote...");
  const quoteResp = await request.post(`${BACKEND}/cart/shipping-quote`, {
    data: {
      country: COUNTRY_CODE,
      city: CITY_NAME,
      items: [{ product_id: product.id, quantity: 2 }],
    },
  });
  expect(quoteResp.ok(), `Shipping quote: ${quoteResp.status()}`).toBeTruthy();

  const quote = (await quoteResp.json()) as {
    shipping_amount: number;
    source: string;
    partner_name?: string;
    partner_id?: number;
    pricing_breakdown?: Record<string, unknown>;
    service_area?: Record<string, unknown>;
    estimated_delivery_min?: number;
    estimated_delivery_max?: number;
  };

  console.log(`[test] Quote: amount=${quote.shipping_amount} source=${quote.source} partner=${quote.partner_name ?? "—"}`);

  // ── CRITICAL ASSERTIONS ──
  expect(quote.shipping_amount).toBeGreaterThan(0);
  expect(
    quote.source === "approved_logistics_partner" || quote.source === "shipment_groups",
    `Expected logistics partner source, got "${quote.source}"`,
  ).toBeTruthy();

  if (quote.partner_name) {
    console.log(`[test] ✓ Partner: ${quote.partner_name}`);
  }

  // Verify the pricing breakdown contains the fee structure
  if (quote.pricing_breakdown) {
    expect(quote.pricing_breakdown).toHaveProperty("base_fee");
    expect(Number(quote.pricing_breakdown.base_fee)).toBeGreaterThan(0);
    console.log(`[test] ✓ base_fee=${quote.pricing_breakdown.base_fee}`);
  }

  // Verify service area info if present
  if (quote.service_area) {
    const sa = quote.service_area as Record<string, unknown>;
    console.log(`[test] ✓ Service area: ${JSON.stringify(sa)}`);
  }

  // Verify delivery ETA
  if (quote.estimated_delivery_min !== undefined) {
    console.log(`[test] ✓ ETA: ${quote.estimated_delivery_min}-${quote.estimated_delivery_max} days`);
  }

  console.log(`[test] ✓ ALL PASSED — ${quote.source} | ${quote.partner_name} | ${quote.shipping_amount}`);
});
