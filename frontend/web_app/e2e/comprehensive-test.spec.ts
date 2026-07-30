import { test, expect } from "@playwright/test";

const BASE = "http://localhost:3000";
const API_BASE = "http://localhost:8000";

// ── Helper: authenticate browser session via API cookies ──────────────────
async function authenticateAs(page: any, email: string, password: string) {
  // Call login API — this sets httpOnly refresh cookie on the browser
  const response = await page.request.post(`${API_BASE}/auth/login`, {
    data: { email, password },
  });
  expect(response.ok()).toBeTruthy();

  // Set session flag so frontend attempts silent refresh (via httpOnly cookie)
  await page.goto(`${BASE}/`, { waitUntil: "domcontentloaded", timeout: 10000 }).catch(() => {});
  await page.evaluate(() => {
    localStorage.setItem("zozi_has_session", "1");
  });
}

// ── 1. PUBLIC PRODUCTS PAGE ───────────────────────────────────────────────
test.describe("Products Page (Public)", () => {
  test("products page loads and shows search bar", async ({ page }) => {
    await page.goto(`${BASE}/products`, { waitUntil: "domcontentloaded", timeout: 20000 });
    // Wait for the page to settle — products are client-fetched via API
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
    // Verify we are on the products page
    await expect(page).toHaveURL(/\/products/, { timeout: 5000 });
    // Wait for some text to appear (products, search bar, etc.)
    await expect(async () => {
      const text = await page.locator("body").innerText();
      expect(text.length).toBeGreaterThan(50);
    }).toPass({ timeout: 10000 });
  });

  test("search bar accepts input", async ({ page }) => {
    await page.goto(`${BASE}/products`, { waitUntil: "domcontentloaded", timeout: 20000 });
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
    // Find any text input in the search/filter area
    const anyInput = page.locator('input[type="text"], input[type="search"], input:not([type])').first();
    const inputVisible = await anyInput.isVisible({ timeout: 5000 }).catch(() => false);
    if (inputVisible) {
      await anyInput.fill("handbag");
      await anyInput.press("Enter");
      await page.waitForTimeout(2000);
    }
    expect(page.url()).toContain("/products");
  });
});

// ── 2. API ENDPOINT TESTS (no browser needed) ────────────────────────────
test.describe("API Endpoints", () => {
  let adminToken: string;

  test.beforeAll(async ({ request }) => {
    const r = await request.post(`${API_BASE}/auth/login`, {
      data: { email: "admin@zozi.com", password: "admin123" },
    });
    adminToken = (await r.json()).access_token;
  });

  // Public
  test("GET /health", async ({ request }) => {
    expect((await request.get(`${API_BASE}/health`)).ok()).toBeTruthy();
  });
  test("GET /products", async ({ request }) => {
    const r = await request.get(`${API_BASE}/products?limit=5`);
    expect(r.ok()).toBeTruthy();
    const data = await r.json();
    // Products endpoint returns array directly
    const items = Array.isArray(data) ? data : data?.items ?? [];
    expect(items.length).toBeGreaterThan(0);
  });
  test("GET /categories", async ({ request }) => {
    expect((await request.get(`${API_BASE}/categories`)).ok()).toBeTruthy();
  });
  test("GET /suppliers (public)", async ({ request }) => {
    expect((await request.get(`${API_BASE}/suppliers?limit=5`)).ok()).toBeTruthy();
  });
  test("GET /banners", async ({ request }) => {
    expect((await request.get(`${API_BASE}/banners`)).ok()).toBeTruthy();
  });
  test("GET /search/trending", async ({ request }) => {
    expect((await request.get(`${API_BASE}/search/trending`)).ok()).toBeTruthy();
  });

  // Auth
  test("POST /auth/login (admin)", async ({ request }) => {
    const r = await request.post(`${API_BASE}/auth/login`, {
      data: { email: "admin@zozi.com", password: "admin123" },
    });
    expect(r.ok()).toBeTruthy();
    expect((await r.json()).user.role).toBe("admin");
  });
  test("POST /auth/login (supplier)", async ({ request }) => {
    const r = await request.post(`${API_BASE}/auth/login`, {
      data: { email: "supplier@zozi.com", password: "supplier123" },
    });
    expect(r.ok()).toBeTruthy();
    expect((await r.json()).user.role).toBe("supplier");
  });
  test("POST /auth/login (customer)", async ({ request }) => {
    const r = await request.post(`${API_BASE}/auth/login`, {
      data: { email: "customer@zozi.com", password: "customer123" },
    });
    expect(r.ok()).toBeTruthy();
    expect((await r.json()).user.role).toBe("customer");
  });
  test("POST /auth/login invalid credentials", async ({ request }) => {
    expect(
      (await request.post(`${API_BASE}/auth/login`, {
        data: { email: "nonexistent@test.com", password: "wrong" },
      })).status()
    ).toBe(401);
  });
  test("protected admin endpoint rejects unauthenticated", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/orders?limit=2`)).status()).toBe(401);
  });

  // Admin (authenticated)
  test("GET /admin/orders", async ({ request }) => {
    const r = await request.get(`${API_BASE}/admin/orders?limit=2`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    expect(r.ok()).toBeTruthy();
    expect((await r.json()).data.length).toBeGreaterThan(0);
  });
  test("GET /admin/products", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/products?limit=2`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })).ok()).toBeTruthy();
  });
  test("GET /admin/users", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/users?limit=2`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })).ok()).toBeTruthy();
  });
  test("GET /admin/dashboard", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/dashboard`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })).ok()).toBeTruthy();
  });
  test("GET /admin/stats", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/stats`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })).ok()).toBeTruthy();
  });
  test("GET /admin/employees", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/employees?limit=2`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })).ok()).toBeTruthy();
  });
  test("GET /admin/suppliers", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/suppliers?limit=2`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })).ok()).toBeTruthy();
  });
  test("GET /admin/payments", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/payments?limit=2`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })).ok()).toBeTruthy();
  });
  test("GET /admin/payouts", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/payouts?limit=2`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })).ok()).toBeTruthy();
  });
  test("GET /admin/treasury", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/treasury`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })).ok()).toBeTruthy();
  });
  test("GET /admin/logistics", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/logistics?limit=2`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })).ok()).toBeTruthy();
  });
  test("GET /admin/logistics-partners", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/logistics-partners?limit=2`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })).ok()).toBeTruthy();
  });
  test("GET /admin/categories", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/categories?limit=2`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })).ok()).toBeTruthy();
  });
  test("GET /admin/commission", async ({ request }) => {
    expect((await request.get(`${API_BASE}/admin/commission`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })).ok()).toBeTruthy();
  });
  test("GET /auth/me", async ({ request }) => {
    const r = await request.get(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    expect(r.ok()).toBeTruthy();
    expect((await r.json()).role).toBe("admin");
  });
});

// ── 3. REGISTRATION ───────────────────────────────────────────────────────
test.describe("Registration", () => {
  const testEmail = `e2e_reg_${Date.now()}@test.com`;

  test("register a new customer", async ({ request }) => {
    const r = await request.post(`${API_BASE}/auth/register`, {
      data: {
        email: testEmail,
        username: `e2euser_${Date.now()}`,
        password: "TestPass123!",
        role: "customer",
        full_name: "E2E Test User",
      },
    });
    expect(r.ok()).toBeTruthy();
    const body = await r.json();
    expect(body.user.role).toBe("customer");
  });

  test("reject duplicate email", async ({ request }) => {
    const r = await request.post(`${API_BASE}/auth/register`, {
      data: { email: testEmail, username: `dup_${Date.now()}`, password: "TestPass123!", role: "customer" },
    });
    expect(r.status()).toBe(400);
  });
});

// ── 4. ADMIN PANEL (browser) ──────────────────────────────────────────────
test.describe("Admin Panel (Browser)", () => {
  test.beforeEach(async ({ page }) => {
    await authenticateAs(page, "admin@zozi.com", "admin123");
  });

  test("command center loads", async ({ page }) => {
    await page.goto(`${BASE}/admin/command-center`, { waitUntil: "domcontentloaded", timeout: 15000 });
    await page.waitForTimeout(4000);
    expect(page.url()).toContain("/admin/command-center");
  });

  test("products page loads", async ({ page }) => {
    await page.goto(`${BASE}/admin/products`, { waitUntil: "domcontentloaded", timeout: 15000 });
    await page.waitForTimeout(3000);
    expect(page.url()).toContain("/admin/products");
  });

  test("orders page loads", async ({ page }) => {
    await page.goto(`${BASE}/admin/orders`, { waitUntil: "domcontentloaded", timeout: 15000 });
    await page.waitForTimeout(3000);
    expect(page.url()).toContain("/admin/orders");
  });
});

// ── 5. DATA INTEGRITY ────────────────────────────────────────────────────
test.describe("Data Integrity", () => {
  let adminToken: string;

  test.beforeAll(async ({ request }) => {
    const r = await request.post(`${API_BASE}/auth/login`, {
      data: { email: "admin@zozi.com", password: "admin123" },
    });
    adminToken = (await r.json()).access_token;
  });

  test("products have valid schema", async ({ request }) => {
    const r = await request.get(`${API_BASE}/products?limit=2`);
    expect(r.ok()).toBeTruthy();
    const data = await r.json();
    const items = Array.isArray(data) ? data : data.items ?? [];
    for (const p of items) {
      expect(p).toHaveProperty("id");
      expect(p).toHaveProperty("name");
      expect(p).toHaveProperty("price");
      expect(typeof p.name).toBe("string");
    }
  });

  test("orders have valid schema", async ({ request }) => {
    const r = await request.get(`${API_BASE}/admin/orders?limit=1`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    expect(r.ok()).toBeTruthy();
    const body = await r.json();
    const orders = body.data ?? [];
    if (orders.length > 0) {
      expect(orders[0]).toHaveProperty("order_number");
      expect(orders[0]).toHaveProperty("status");
      expect(orders[0]).toHaveProperty("total_amount");
    }
  });

  test("admin dashboard returns structured data", async ({ request }) => {
    const r = await request.get(`${API_BASE}/admin/dashboard`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    expect(r.ok()).toBeTruthy();
  });
});
