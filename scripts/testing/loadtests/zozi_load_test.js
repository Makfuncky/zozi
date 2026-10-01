import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const CUSTOMER_EMAIL = __ENV.CUSTOMER_EMAIL || "customer@zozi.com";
const CUSTOMER_PASSWORD = __ENV.CUSTOMER_PASSWORD || "customer123";
const WEBHOOK_SECRET = __ENV.WEBHOOK_SECRET || "dev-webhook-secret";
const PRODUCT_ID = __ENV.PRODUCT_ID || "";

function login(email, password) {
  const response = http.post(
    `${BASE_URL}/auth/login`,
    `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
  );
  if (response.status !== 200) {
    return "";
  }
  return response.json("access_token") || "";
}

function resolveProductIds() {
  if (PRODUCT_ID) {
    return [String(PRODUCT_ID)];
  }
  const response = http.get(`${BASE_URL}/products?limit=50&sort=newest`);
  if (response.status !== 200) {
    return ["1"];
  }
  const body = response.json();
  const products = body?.data || body?.products || body?.items || body || [];
  if (!Array.isArray(products) || products.length === 0) {
    return ["1"];
  }
  const candidateIds = products
    .filter((p) => Number(p?.stock || 0) > 0)
    .sort((a, b) => Number(b?.stock || 0) - Number(a?.stock || 0))
    .slice(0, 10)
    .map((p) => String(p?.id || 1));
  return candidateIds.length > 0 ? candidateIds : ["1"];
}

export const options = {
  scenarios: {
    browse_products: {
      executor: "ramping-vus",
      exec: "browseScenario",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 100 },
        { duration: "4m", target: 100 },
        { duration: "30s", target: 0 },
      ],
    },
    checkout_flow: {
      executor: "ramping-vus",
      exec: "checkoutScenario",
      startVUs: 0,
      startTime: "10s",
      stages: [
        { duration: "30s", target: 50 },
        { duration: "4m", target: 50 },
        { duration: "30s", target: 0 },
      ],
    },
    payment_webhooks: {
      executor: "constant-arrival-rate",
      exec: "webhookScenario",
      rate: 10,
      timeUnit: "1s",
      duration: "3m",
      preAllocatedVUs: 20,
      maxVUs: 50,
      startTime: "20s",
    },
  },
  thresholds: {
    checks: ["rate>0.99"],
    http_req_failed: ["rate<0.02"],
    http_req_duration: ["p(95)<1200"],
    "http_req_duration{scenario:browse_products}": ["p(95)<800"],
    "http_req_duration{scenario:checkout_flow}": ["p(95)<1500"],
    "http_req_duration{scenario:payment_webhooks}": ["p(95)<500"],
  },
};

export function setup() {
  return {
    customerToken: login(CUSTOMER_EMAIL, CUSTOMER_PASSWORD),
    productIds: resolveProductIds(),
  };
}

export function browseScenario() {
  const response = http.get(`${BASE_URL}/products?limit=24&sort=newest`);
  check(response, {
    "browse status is 200": (r) => r.status === 200,
    "browse returns products": (r) => {
      const body = r.json();
      return Array.isArray(body?.data || body?.products || body?.items);
    },
  });
  sleep(1);
}

export function checkoutScenario(data) {
  const productIds = (data && data.productIds) || ["1"];
  const selectedId = productIds[(__VU + __ITER) % productIds.length] || productIds[0];
  const payload = JSON.stringify({
    items: [{ product_id: Number(selectedId), quantity: 1 }],
    full_name: "Load Test Customer",
    street: "123 Load Street",
    city: "Muscat",
    zip: "100",
    country: "OM",
    payment_method: "cod",
  });
  const token = (data && data.customerToken) || "";
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = http.post(`${BASE_URL}/orders/`, payload, { headers });
  check(response, {
    "checkout accepted": (r) => r.status === 200 || r.status === 201,
  });
  sleep(2);
}

export function webhookScenario() {
  const payload = JSON.stringify({
    id: `evt_k6_${__VU}_${__ITER}`,
    type: "payment_intent.succeeded",
    data: { object: { id: `pi_k6_${__VU}_${__ITER}` } },
  });
  const response = http.post(`${BASE_URL}/payments/webhook`, payload, {
    headers: {
      "Content-Type": "application/json",
      "Stripe-Signature": WEBHOOK_SECRET,
    },
  });
  check(response, {
    "webhook reachable": (r) => r.status < 500,
  });
}
