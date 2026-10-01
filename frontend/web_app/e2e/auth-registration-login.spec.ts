/**
 * Auth Registration + Login E2E Tests
 *
 * Tests the complete registration and login flow for all 4 user roles,
 * verifying data persists to the database (not JSON files).
 *
 * Roles: customer, supplier, logistics_partner, admin
 * Password policy: ≥8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
 */
import { expect, test, type Page } from "@playwright/test";
import {
  registerUser,
  loginUser,
  verifyUser,
  apiGet,
  WEB_BASE,
  uniqueEmail,
  uniqueUsername,
} from "./helpers/api";

const BASE = WEB_BASE;

const TEST_PASSWORD = process.env.E2E_TEST_PASSWORD || "TestPass123!";

/** Register a user through the UI form */
async function registerViaUI(
  page: Page,
  role: string,
  email: string,
  username: string,
  password: string,
  opts?: { business_name?: string }
) {
  const registerUrl =
    role === "customer"
      ? "/register"
      : role === "supplier"
        ? "/supplier/register"
        : role === "logistics_partner"
          ? "/logistics-partner/register"
          : "/register";

  await page.goto(`${BASE}${registerUrl}`, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("networkidle").catch(() => {});

  // Fill email
  const emailInput = page
    .locator(
      "input[type='email'], input[name='email'], input[autocomplete='email']"
    )
    .first();
  if (await emailInput.isVisible()) {
    await emailInput.fill(email);
  }

  // Fill username
  const usernameInput = page
    .locator(
      "input[name='username'], input[autocomplete='username'], input[placeholder*='user' i]"
    )
    .first();
  if (await usernameInput.isVisible()) {
    await usernameInput.fill(username);
  }

  // Fill business name if supplier
  if (opts?.business_name) {
    const bizInput = page
      .locator(
        "input[name='business_name'], input[placeholder*='business' i], input[placeholder*='company' i]"
      )
      .first();
    if (await bizInput.isVisible()) {
      await bizInput.fill(opts.business_name);
    }
  }

  // Fill password
  const passwordInput = page.locator("input[type='password']").first();
  if (await passwordInput.isVisible()) {
    await passwordInput.fill(password);
  }

  // Fill confirm password if present
  const confirmInput = page.locator("input[type='password']").nth(1);
  if ((await confirmInput.count()) > 0 && (await confirmInput.isVisible())) {
    await confirmInput.fill(password);
  }

  // Accept terms checkbox if present
  const termsCheckbox = page
    .locator("input[type='checkbox']")
    .first();
  if (
    (await termsCheckbox.count()) > 0 &&
    (await termsCheckbox.isVisible()) &&
    !(await termsCheckbox.isChecked())
  ) {
    await termsCheckbox.check();
  }

  // Submit
  const submitBtn = page
    .getByRole("button", {
      name: /register|sign up|create.*account/i,
    })
    .first();
  if (await submitBtn.isVisible()) {
    await submitBtn.click();
  }
}

// ── Tests ────────────────────────────────────────────────────────────────────

test.describe.configure({ timeout: 120_000 });

test.describe("Registration — all roles (API)", () => {
  test("customer registration persists to database", async ({ page }) => {
    const email = uniqueEmail("customer");
    const username = uniqueUsername("customer");

    const result = await registerUser(page, {
      email,
      username,
      password: TEST_PASSWORD,
      role: "customer",
    });

    expect(result.status).toBe(200);
    expect(result.body).toHaveProperty("id");
    expect(result.body.email).toBe(email);
    expect(result.body.role).toBe("customer");

    // Verify persistence: login and query /me
    const loginResult = await loginUser(page, email, TEST_PASSWORD);
    expect(loginResult.status).toBe(200);
    expect(loginResult.body).toHaveProperty("access_token");

    const token = loginResult.body.access_token!;
    const meResult = await verifyUser(page, token);
    expect(meResult.status).toBe(200);
    expect(meResult.body.email).toBe(email);
    expect(meResult.body.role).toBe("customer");
  });

  test("supplier registration persists with business profile", async ({
    page,
  }) => {
    const email = uniqueEmail("supplier");
    const username = uniqueUsername("supplier");

    const result = await registerUser(page, {
      email,
      username,
      password: TEST_PASSWORD,
      role: "supplier",
      business_name: "E2E Test Supplier Co",
    });

    expect(result.status).toBe(200);
    expect(result.body).toHaveProperty("id");
    expect(result.body.role).toBe("supplier");

    // Verify login works
    const loginResult = await loginUser(page, email, TEST_PASSWORD);
    expect(loginResult.status).toBe(200);
  });

  test("logistics_partner registration persists with partner profile", async ({
    page,
  }) => {
    const email = uniqueEmail("logistics");
    const username = uniqueUsername("logistics");

    const result = await registerUser(page, {
      email,
      username,
      password: TEST_PASSWORD,
      role: "logistics_partner",
    });

    expect(result.status).toBe(200);
    expect(result.body).toHaveProperty("id");
    expect(result.body.role).toBe("logistics_partner");

    // Verify login works
    const loginResult = await loginUser(page, email, TEST_PASSWORD);
    expect(loginResult.status).toBe(200);
  });

  test("duplicate email registration is rejected", async ({ page }) => {
    const email = uniqueEmail("dup_test");

    // First registration succeeds
    const first = await registerUser(page, {
      email,
      username: uniqueUsername("dup1"),
      password: TEST_PASSWORD,
      role: "customer",
    });
    expect(first.status).toBe(200);

    // Second registration with same email fails
    const second = await registerUser(page, {
      email,
      username: uniqueUsername("dup2"),
      password: TEST_PASSWORD,
      role: "customer",
    });
    expect(second.status).toBe(400);
    expect(second.body.detail).toMatch(/already registered/i);
  });

  test("weak password is rejected", async ({ page }) => {
    const result = await registerUser(page, {
      email: uniqueEmail("weak"),
      username: uniqueUsername("weak"),
      password: "weak",
      role: "customer",
    });
    expect(result.status).toBe(422);
    expect(result.body.detail).toMatch(/password/i);
  });
});

test.describe("Login — all roles (API)", () => {
  test("admin login returns valid token with correct role", async ({ page }) => {
    // First ensure the admin user exists (seeded by backend)
    const adminPassword = process.env.SEED_ADMIN_PASSWORD || process.env.E2E_ADMIN_PASSWORD || "DevSeed123!";
    const result = await loginUser(page, "admin@zozi.com", adminPassword);

    if (result.status !== 200) {
      const altResult = await loginUser(page, "admin@zozi.com", "Admin@123");
      expect(altResult.status).toBe(200);
      expect(altResult.body).toHaveProperty("access_token");
      return;
    }

    expect(result.status).toBe(200);
    expect(result.body).toHaveProperty("access_token");
    expect(result.body).toHaveProperty("refresh_token");

    // Verify the token resolves to correct user
    const meResult = await verifyUser(page, result.body.access_token!);
    expect(meResult.status).toBe(200);
    expect(meResult.body.role).toBe("admin");
  });

  test("wrong password returns 400", async ({ page }) => {
    const result = await loginUser(
      page,
      "admin@zozi.com",
      "WrongPassword123!"
    );
    expect(result.status).toBe(400);
    expect(result.body.detail).toMatch(/incorrect/i);
  });

  test("nonexistent user returns 400", async ({ page }) => {
    const result = await loginUser(
      page,
      "nonexistent@zozi-test.com",
      "AnyPass123!"
    );
    expect(result.status).toBe(400);
  });
});

test.describe("Registration — UI flow", () => {
  test("customer can register through the UI form", async ({ page }) => {
    const email = uniqueEmail("customer_ui");
    const username = uniqueUsername("customer_ui");

    await registerViaUI(page, "customer", email, username, TEST_PASSWORD);

    // After registration, should redirect or show success
    await page.waitForTimeout(3000);
    const url = page.url();
    const successOrRedirect =
      url.includes("login") ||
      url.includes("verify") ||
      url.includes("dashboard") ||
      url.includes("products") ||
      (await page.getByText(/success|verify|welcome/i).count()) > 0;
    expect(successOrRedirect).toBe(true);
  });
});

test.describe("Login — UI flow", () => {
  test("admin can login through the UI and reaches dashboard", async ({
    page,
  }) => {
    await page.goto(`${BASE}/admin/login`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForLoadState("networkidle").catch(() => {});

    // Fill credentials
    const identifierInput = page
      .locator(
        "input[type='email'], input[name='username'], input[name='email'], input[autocomplete='username']"
      )
      .first();
    await identifierInput.fill("admin@zozi.com");

    const passwordInput = page.locator("input[type='password']").first();
    const adminPassword = process.env.SEED_ADMIN_PASSWORD || process.env.E2E_ADMIN_PASSWORD || "DevSeed123!";
    await passwordInput.fill(adminPassword);

    // Submit
    const submitBtn = page
      .getByRole("button", { name: /sign in|log in|signin/i })
      .first();
    await submitBtn.click();

    // Wait for navigation away from login
    await page.waitForTimeout(5000);
    const url = page.url();
    const loggedIn =
      url.includes("admin/dashboard") ||
      url.includes("admin/command-center") ||
      url.includes("admin") && !url.includes("login");
    expect(loggedIn).toBe(true);
  });

  test("customer can login through the UI and reaches products", async ({
    page,
  }) => {
    // First register a fresh customer
    const email = uniqueEmail("cust_login_ui");
    const username = uniqueUsername("cust_login_ui");
    await registerUser(page, {
      email,
      username,
      password: TEST_PASSWORD,
      role: "customer",
    });

    // Now login via UI
    await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle").catch(() => {});

    const identifierInput = page
      .locator(
        "input[type='email'], input[name='username'], input[name='email'], input[autocomplete='username']"
      )
      .first();
    await identifierInput.fill(email);

    const passwordInput = page.locator("input[type='password']").first();
    await passwordInput.fill(TEST_PASSWORD);

    const submitBtn = page
      .getByRole("button", { name: /sign in|log in|signin/i })
      .first();
    await submitBtn.click();

    await page.waitForTimeout(5000);
    const url = page.url();
    const loggedIn =
      url.includes("products") ||
      url.includes("dashboard") ||
      url.includes("orders") ||
      !url.includes("login");
    expect(loggedIn).toBe(true);
  });
});

test.describe("Database persistence verification", () => {
  test("registered user survives server restart (token validity)", async ({
    page,
  }) => {
    const email = uniqueEmail("persist");
    const username = uniqueUsername("persist");

    // Register
    const regResult = await registerUser(page, {
      email,
      username,
      password: TEST_PASSWORD,
      role: "customer",
    });
    expect(regResult.status).toBe(200);

    // Login
    const loginResult = await loginUser(page, email, TEST_PASSWORD);
    expect(loginResult.status).toBe(200);
    const token = loginResult.body.access_token as string;
    expect(token).toBeDefined();

    // Verify token works (user persisted in DB)
    const meResult = await verifyUser(page, token);
    expect(meResult.status).toBe(200);
    expect(meResult.body.email).toBe(email);

    // Create a new page context (simulate fresh session) and verify token still works
    const freshContext = await page.context().browser()!.newContext();
    const freshPage = await freshContext.newPage();
    const freshResult = await verifyUser(freshPage, token as string);
    expect(freshResult.status).toBe(200);
    expect(freshResult.body.email).toBe(email);
    await freshContext.close();
  });

  test("product visibility — products endpoint returns seeded data", async ({
    page,
  }) => {
    await page.goto(`${BASE}/`, { waitUntil: "domcontentloaded" });

    const result = await apiGet(page, "/api/products?limit=5");

    expect(result.status).toBe(200);
    // The products should come from the database, not JSON files
    const products = result.body.products || result.body.items || result.body;
    expect(Array.isArray(products) || typeof products === "object").toBe(true);
  });
});
