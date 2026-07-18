import http from "k6/http";
import { check, group, sleep } from "k6";

const LOAD_PROFILE = (__ENV.LOAD_PROFILE || "baseline").toLowerCase();
const SCALE_MAX_VUS = Number(__ENV.SCALE_MAX_VUS || 1000);

function toInt(value, fallbackValue) {
  const parsed = Number(value);
  if (Number.isFinite(parsed) && parsed > 0) {
    return Math.floor(parsed);
  }
  return fallbackValue;
}

function buildScenarios(profile) {
  if (profile === "scale1000") {
    const targetVus = toInt(SCALE_MAX_VUS, 1000);
    const browseVus = Math.max(300, Math.round(targetVus * 0.65));
    const searchVus = Math.max(120, Math.round(targetVus * 0.22));
    const checkoutVus = Math.max(50, Math.round(targetVus * 0.1));
    const adminVus = Math.max(20, Math.round(targetVus * 0.03));

    return {
      login: {
        executor: "constant-arrival-rate",
        exec: "loginScenario",
        rate: 40,
        timeUnit: "1s",
        duration: "12m",
        preAllocatedVUs: 120,
        maxVUs: 450,
      },
      browse: {
        executor: "ramping-vus",
        exec: "browseScenario",
        startVUs: 0,
        stages: [
          { duration: "2m", target: Math.round(browseVus * 0.4) },
          { duration: "4m", target: browseVus },
          { duration: "5m", target: browseVus },
          { duration: "1m", target: 0 },
        ],
      },
      search: {
        executor: "ramping-vus",
        exec: "searchScenario",
        startVUs: 0,
        startTime: "30s",
        stages: [
          { duration: "2m", target: Math.round(searchVus * 0.4) },
          { duration: "4m", target: searchVus },
          { duration: "5m", target: searchVus },
          { duration: "1m", target: 0 },
        ],
      },
      checkout: {
        executor: "constant-vus",
        exec: "checkoutScenario",
        vus: checkoutVus,
        duration: "11m",
        startTime: "1m",
      },
      webhook: {
        executor: "constant-arrival-rate",
        exec: "webhookScenario",
        rate: 20,
        timeUnit: "1s",
        duration: "11m",
        preAllocatedVUs: 60,
        maxVUs: 220,
        startTime: "1m",
      },
      admin: {
        executor: "constant-vus",
        exec: "adminScenario",
        vus: adminVus,
        duration: "11m",
        startTime: "1m",
      },
    };
  }

  return {
    login: {
      executor: "constant-arrival-rate",
      exec: "loginScenario",
      rate: 2,
      timeUnit: "1s",
      duration: "60s",
      preAllocatedVUs: 4,
      maxVUs: 20,
    },
    browse: {
      executor: "ramping-vus",
      exec: "browseScenario",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 10 },
        { duration: "2m", target: 25 },
        { duration: "30s", target: 0 },
      ],
    },
    search: {
      executor: "ramping-vus",
      exec: "searchScenario",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 10 },
        { duration: "2m", target: 20 },
        { duration: "30s", target: 0 },
      ],
    },
    checkout: {
      executor: "constant-vus",
      exec: "checkoutScenario",
      vus: 3,
      duration: "90s",
      startTime: "10s",
    },
    webhook: {
      executor: "constant-arrival-rate",
      exec: "webhookScenario",
      rate: 5,
      timeUnit: "1s",
      duration: "60s",
      preAllocatedVUs: 5,
      maxVUs: 30,
      startTime: "15s",
    },
    admin: {
      executor: "constant-vus",
      exec: "adminScenario",
      vus: 4,
      duration: "90s",
      startTime: "20s",
    },
  };
}

function buildThresholds(profile) {
  if (profile === "scale1000") {
    return {
      checks: ["rate>0.97"],
      http_req_failed: ["rate<0.03"],
      http_req_duration: ["p(90)<1800", "p(95)<2500", "p(99)<4000"],
      "http_req_duration{scenario:checkout}": ["p(95)<3200"],
    };
  }

  return {
    checks: ["rate>0.99"],
    http_req_failed: ["rate<0.02"],
    http_req_duration: ["p(95)<1200"],
  };
}

export const options = {
  scenarios: buildScenarios(LOAD_PROFILE),
  thresholds: buildThresholds(LOAD_PROFILE),
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const ADMIN_TOKEN = __ENV.ADMIN_TOKEN || "";
const CUSTOMER_TOKEN = __ENV.CUSTOMER_TOKEN || "";
const PRODUCT_ID = __ENV.PRODUCT_ID || "";
const WEBHOOK_SECRET = __ENV.WEBHOOK_SECRET || "dev-webhook-secret";
const ADMIN_EMAIL = __ENV.ADMIN_EMAIL || "admin@zozi.com";
const ADMIN_PASSWORD = __ENV.ADMIN_PASSWORD || "admin123";
const CUSTOMER_EMAIL = __ENV.CUSTOMER_EMAIL || "customer@zozi.com";
const CUSTOMER_PASSWORD = __ENV.CUSTOMER_PASSWORD || "customer123";
const WEBHOOK_EXPECTED_STATUSES = http.expectedStatuses(200, 400);

function jsonHeaders(token) {
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

function login(email, password) {
  const response = http.post(
    `${BASE_URL}/auth/login`,
    `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    }
  );
  check(response, {
    [`login ok ${email}`]: (res) => res.status === 200,
  });
  if (response.status !== 200) {
    return "";
  }
  return response.json("access_token") || "";
}

function resolveCheckoutProductIds() {
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
    .filter((product) => Number(product?.stock || 0) > 0)
    .sort((left, right) => Number(right?.stock || 0) - Number(left?.stock || 0))
    .slice(0, 10)
    .map((product) => String(product?.id || 1));
  return candidateIds.length > 0 ? candidateIds : ["1"];
}

export function setup() {
  return {
    adminToken: ADMIN_TOKEN || login(ADMIN_EMAIL, ADMIN_PASSWORD),
    customerToken: CUSTOMER_TOKEN || login(CUSTOMER_EMAIL, CUSTOMER_PASSWORD),
    productIds: resolveCheckoutProductIds(),
  };
}

export function loginScenario() {
  group("login", () => {
    const customerToken = login(CUSTOMER_EMAIL, CUSTOMER_PASSWORD);
    const adminToken = login(ADMIN_EMAIL, ADMIN_PASSWORD);
    check({ customerToken, adminToken }, {
      "customer login token issued": (tokens) => Boolean(tokens.customerToken),
      "admin login token issued": (tokens) => Boolean(tokens.adminToken),
    });
    sleep(1);
  });
}

export function browseScenario(data) {
  group("browse", () => {
    const response = http.get(`${BASE_URL}/products?limit=24&sort=newest`);
    check(response, {
      "browse list ok": (res) => res.status === 200,
    });
    sleep(1);
  });
}

export function searchScenario() {
  group("search", () => {
    const response = http.get(`${BASE_URL}/search/products?q=headphones&limit=12`);
    check(response, {
      "search ok": (res) => res.status === 200,
      "search returns payload": (res) => {
        const body = res.json();
        return Array.isArray(body?.results || body?.products);
      },
    });
    sleep(1);
  });
}

export function checkoutScenario(data) {
  group("checkout", () => {
    const productIds = (data && data.productIds) || (PRODUCT_ID ? [String(PRODUCT_ID)] : ["1"]);
    const selectedProductId = Number(productIds[(__VU + __ITER) % productIds.length] || productIds[0] || 1);
    const payload = {
      items: [
        {
          product_id: selectedProductId,
          quantity: 1,
        },
      ],
      full_name: "Load Test Customer",
      street: "123 Load Street",
      city: "Muscat",
      zip: "100",
      country: "OM",
      payment_method: "cod",
    };
    const response = http.post(`${BASE_URL}/orders/`, JSON.stringify(payload), {
      headers: jsonHeaders((data && data.customerToken) || CUSTOMER_TOKEN),
    });
    check(response, {
      "checkout accepted": (res) => res.status === 200 || res.status === 201,
    });
    sleep(2);
  });
}

export function webhookScenario() {
  group("webhook", () => {
    const response = http.post(
      `${BASE_URL}/payments/webhook`,
      JSON.stringify({ id: `evt_k6_${__VU}_${__ITER}`, type: "payment_intent.succeeded", data: { object: { id: `pi_k6_${__VU}_${__ITER}` } } }),
      {
        responseCallback: WEBHOOK_EXPECTED_STATUSES,
        headers: {
          "Content-Type": "application/json",
          "Stripe-Signature": WEBHOOK_SECRET,
        },
      }
    );
    check(response, {
      "webhook endpoint reachable": (res) => res.status < 500,
    });
  });
}

export function adminScenario(data) {
  group("admin", () => {
    const analytics = http.get(`${BASE_URL}/admin/analytics`, {
      headers: jsonHeaders((data && data.adminToken) || ADMIN_TOKEN),
    });
    const orders = http.get(`${BASE_URL}/admin/orders?page=1&page_size=100`, {
      headers: jsonHeaders((data && data.adminToken) || ADMIN_TOKEN),
    });
    check(analytics, { "admin analytics ok": (res) => res.status === 200 });
    check(orders, { "admin orders reachable": (res) => res.status === 200 });
    sleep(1);
  });
}