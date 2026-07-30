import { test, expect } from "@playwright/test";

const BASE = "http://localhost:3000";
const API_BASE = "http://localhost:8000";

test.describe("Frontend Browser Tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 15000 });
  });

  test("home page loads successfully", async ({ page }) => {
    const response = await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 15000 });
    expect(response?.status()).toBe(200);
  });

  test("login page loads successfully", async ({ page }) => {
    const response = await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded", timeout: 15000 });
    expect(response?.status()).toBe(200);
  });

  test("admin login page loads successfully", async ({ page }) => {
    const response = await page.goto(`${BASE}/admin/login`, { waitUntil: "domcontentloaded", timeout: 15000 });
    expect(response?.status()).toBe(200);
  });

  test("logistics partner login page loads successfully", async ({ page }) => {
    const response = await page.goto(`${BASE}/logistics-partner/login`, { waitUntil: "domcontentloaded", timeout: 15000 });
    expect(response?.status()).toBe(200);
  });

  test("supplier login page loads successfully", async ({ page }) => {
    const response = await page.goto(`${BASE}/supplier/login`, { waitUntil: "domcontentloaded", timeout: 15000 });
    expect(response?.status()).toBe(200);
  });

  test("products page loads successfully", async ({ page }) => {
    const response = await page.goto(`${BASE}/products`, { waitUntil: "domcontentloaded", timeout: 15000 });
    expect(response?.status()).toBe(200);
  });

  test("cart page loads successfully", async ({ page }) => {
    const response = await page.goto(`${BASE}/cart`, { waitUntil: "domcontentloaded", timeout: 15000 });
    expect(response?.status()).toBe(200);
  });

  test("checkout page loads successfully", async ({ page }) => {
    const response = await page.goto(`${BASE}/checkout`, { waitUntil: "domcontentloaded", timeout: 15000 });
    expect(response?.status()).toBe(200);
  });

  test("register page loads successfully", async ({ page }) => {
    const response = await page.goto(`${BASE}/register`, { waitUntil: "domcontentloaded", timeout: 15000 });
    expect(response?.status()).toBe(200);
  });

  test("supplier dashboard page loads successfully", async ({ page }) => {
    const response = await page.goto(`${BASE}/supplier/dashboard`, { waitUntil: "domcontentloaded", timeout: 15000 });
    expect(response?.status()).toBe(200);
  });

  test("admin dashboard page loads successfully", async ({ page }) => {
    const response = await page.goto(`${BASE}/admin/dashboard`, { waitUntil: "domcontentloaded", timeout: 15000 });
    expect(response?.status()).toBe(200);
  });

  test("logistics partner dashboard page loads successfully", async ({ page }) => {
    const response = await page.goto(`${BASE}/logistics-partner/dashboard`, { waitUntil: "domcontentloaded", timeout: 15000 });
    expect(response?.status()).toBe(200);
  });

  test("API health endpoint returns 200", async ({ page, request }) => {
    const response = await request.get(`${API_BASE}/health`);
    expect(response.status()).toBe(200);
  });

  test("API auth login endpoint responds", async ({ page, request }) => {
    const response = await request.post(`${API_BASE}/auth/login`, {
      data: { email: "test@example.com", password: "wrongpassword" },
    });
    expect([200, 401]).toContain(response.status());
  });
});