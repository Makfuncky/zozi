/**
 * Admin HR & Permissions — Playwright E2E Tests
 *
 * Covers /admin/staff (staff directory) and /admin/permissions
 * (permission categories, roles, user overrides).
 */
import { expect, test, type Page, type Route } from "@playwright/test";
import { bootstrapAdminSessionViaApi } from "./helpers/auth";

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function mockAdminSession(page: Page) {
  await page.context().clearCookies();
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.evaluate(() => window.localStorage.removeItem("zozi_has_session")).catch(() => undefined);

  for (const candidate of ["admin@zozi.com", "admin"]) {
    await bootstrapAdminSessionViaApi(page);

    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    await page.goto("/admin/staff", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const gate = page.getByRole("heading", { name: /Admin Access/i });
    if (!(await gate.isVisible().catch(() => false))) {
      await page.route("**/cart/**", async (r) => fulfillJson(r, []));
      await page.route("**/notifications**", async (r) => fulfillJson(r, []));
      await page.route("**/api/notifications**", async (r) => fulfillJson(r, []));
      return;
    }
  }

  await page.goto("/admin/login", { waitUntil: "domcontentloaded", timeout: 120_000 });
  const btn = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await btn.waitFor();
  const form = btn.locator("xpath=ancestor::form[1]");
  await form.locator("input:not([type='password']):visible").first().fill("admin@zozi.com");
  await form.locator("input[type='password']:visible").first().fill("admin123");
  await btn.click();
  await page.waitForTimeout(5000);
  await page.goto("/admin/staff", { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.route("**/cart/**", async (r) => fulfillJson(r, []));
  await page.route("**/notifications**", async (r) => fulfillJson(r, []));
  await page.route("**/api/notifications**", async (r) => fulfillJson(r, []));
}

test.describe("Admin HR & Permissions", () => {
  let staff: any[];
  let categories: any[];

  test.beforeEach(async ({ page }) => {
    staff = [
      { id: 1, full_name: "Alice Admin", username: "alice", email: "alice@zozi.com", base_role: "admin", custom_role: "Ops Lead", department: "Operations", area: "UAE", is_active: true, hire_date: "2025-01-15" },
      { id: 2, full_name: "Bob Support", username: "bob", email: "bob@zozi.com", base_role: "support", custom_role: "Tier 1", department: "Support", area: "GCC", is_active: true, hire_date: "2025-03-20" },
    ];

    categories = [
      { id: 1, name: "Inventory Management", slug: "inventory", description: "Manage inventory", icon: "Package", permissions: [
        { id: 1, name: "View Inventory", slug: "inventory.view", description: "Can view inventory", scope: "global" },
        { id: 2, name: "Edit Inventory", slug: "inventory.edit", description: "Can edit inventory", scope: "global" },
      ] },
      { id: 2, name: "Order Management", slug: "orders", description: "Manage orders", icon: "ShoppingCart", permissions: [
        { id: 3, name: "View Orders", slug: "orders.view", description: "Can view orders", scope: "global" },
      ] },
    ];

    // Staff endpoints
    await page.route("**/admin/staff", async (route) => {
      if (route.request().method() === "GET") {
        await fulfillJson(route, staff);
      } else {
        const body = route.request().postDataJSON();
        const newStaff = {
          id: staff.length + 1,
          full_name: body.full_name || body.username,
          username: body.username,
          email: body.email,
          base_role: body.base_role || "support",
          custom_role: body.custom_role || null,
          department: body.department,
          area: body.area,
          is_active: true,
          hire_date: body.hire_date,
        };
        staff.push(newStaff);
        await fulfillJson(route, newStaff, 201);
      }
    });

    await page.route("**/admin/staff/permission-catalog", async (route) => {
      await fulfillJson(route, categories.flatMap((c) => c.permissions));
    });

    // Permission endpoints
    await page.route("**/permissions/categories", async (route) => {
      if (route.request().method() === "GET") {
        await fulfillJson(route, categories);
      } else {
        const body = route.request().postDataJSON();
        const newCat = {
          id: categories.length + 1,
          name: body.name,
          slug: body.slug || body.name.toLowerCase().replace(/\s+/g, "-"),
          description: body.description,
          icon: body.icon,
          permissions: [],
        };
        categories.push(newCat);
        await fulfillJson(route, newCat, 201);
      }
    });

    await page.route("**/permissions/list", async (route) => {
      await fulfillJson(route, categories.flatMap((c) => c.permissions));
    });

    await page.route("**/permissions/roles/**", async (route) => {
      await fulfillJson(route, [
        { permission_id: 1, is_granted: true },
        { permission_id: 3, is_granted: true },
      ]);
    });

    await mockAdminSession(page);
  });

  // ═══════════════ Staff Directory ═══════════════

  test("staff directory lists staff and supports create", async ({ page }) => {
    await page.waitForTimeout(2000);
    await expect(page.getByText(/Staff Directory/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByRole("button", { name: /add staff member/i })).toBeVisible();

    await page.getByText(/Alice Admin/i).first().waitFor({ state: "visible", timeout: 5000 });

    await page.getByRole("button", { name: /add staff member/i }).click();
    await expect(page.getByText(/Create Staff|New Staff Assignment/i)).toBeVisible({ timeout: 5000 });

    await page.getByPlaceholder(/Returns Command Lead/i).fill("QA Lead");
    await page.getByPlaceholder(/At least 8 chars/i).fill("StaffPass123!");
    const createBtn = page.getByRole("button", { name: /create staff/i });
    await createBtn.click();
    await page.waitForTimeout(1000);
  });

  // ═══════════════ Permissions ═══════════════

  test("permissions categories tab lists categories and supports create", async ({ page }) => {
    await page.goto("/admin/permissions", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await page.waitForTimeout(2000);

    await expect(page.getByText(/Permissions/i)).toBeVisible({ timeout: 5000 });
    await page.getByRole("tab", { name: /categories/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByRole("button", { name: /new category/i })).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/Inventory Management/i)).toBeVisible();

    await page.getByRole("button", { name: /new category/i }).click();
    await expect(page.getByText(/New Permission Category/i)).toBeVisible({ timeout: 5000 });

    await page.getByPlaceholder(/e\.g\., Inventory Management/i).fill("Customer Support");
    await page.getByRole("button", { name: /create category/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByText(/Customer Support/i)).toBeVisible();
  });

  test("permissions roles tab shows role permission matrix", async ({ page }) => {
    await page.goto("/admin/permissions", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await page.waitForTimeout(2000);

    await page.getByRole("tab", { name: /roles/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByRole("button", { name: /^admin$/i })).toBeVisible({ timeout: 5000 });
  });
});

