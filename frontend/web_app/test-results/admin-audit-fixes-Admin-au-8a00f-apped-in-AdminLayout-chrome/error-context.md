# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin-audit-fixes.spec.ts >> Admin audit fixes >> audit-logs page is wrapped in AdminLayout chrome
- Location: e2e\admin-audit-fixes.spec.ts:9:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('link', { name: /Command Center/i }).first()
Expected: visible
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 60000ms
  - waiting for getByRole('link', { name: /Command Center/i }).first()

```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | import { bootstrapAdminSessionViaApi } from "./helpers/auth";
  3  | 
  4  | test.describe("Admin audit fixes", () => {
  5  |   test.beforeEach(async ({ page }) => {
  6  |     await bootstrapAdminSessionViaApi(page);
  7  |   });
  8  | 
  9  |   test("audit-logs page is wrapped in AdminLayout chrome", async ({ page }) => {
  10 |     await page.goto("/admin/audit-logs", { waitUntil: "domcontentloaded", timeout: 120_000 });
  11 | 
  12 |     // The bare stub had no AdminLayout; now the admin sidebar nav must render.
  13 |     await expect(
  14 |       page.getByRole("link", { name: /Command Center/i }).first(),
> 15 |     ).toBeVisible({ timeout: 60_000 });
     |       ^ Error: expect(locator).toBeVisible() failed
  16 | 
  17 |     // And the page heading is present (not the old raw <div>Audit logs content</div>).
  18 |     await expect(
  19 |       page.getByRole("heading", { name: "Audit Logs", exact: true }).first(),
  20 |     ).toBeVisible({ timeout: 30_000 });
  21 | 
  22 |     await page.screenshot({ path: "audit-logs-fixed.png", fullPage: true });
  23 |   });
  24 | 
  25 |   test("command-center renders after WebSocket client fix (no regression)", async ({ page }) => {
  26 |     await page.goto("/admin/command-center", { waitUntil: "domcontentloaded", timeout: 180_000 });
  27 | 
  28 |     await expect(
  29 |       page.getByRole("heading", { name: "Command Center", exact: true }).first(),
  30 |     ).toBeVisible({ timeout: 60_000 });
  31 | 
  32 |     await expect(
  33 |       page.getByText(/SYNC|INITIALISING|TELEMETRY LINK LOST/i).first(),
  34 |     ).toBeVisible({ timeout: 30_000 });
  35 | 
  36 |     await page.screenshot({ path: "command-center-fixed.png", fullPage: true });
  37 |   });
  38 | 
  39 |   test("promotions API uses the correct /admin/promotions prefix", async ({ page }) => {
  40 |     await bootstrapAdminSessionViaApi(page);
  41 | 
  42 |     // The promotions page must load its flash-sales panel without routing errors.
  43 |     // Authenticate the page FIRST (it performs its own silent refresh) so the
  44 |     // refresh cookie is not consumed before the page loads — otherwise the page's
  45 |     // own silent refresh would send an already-used token and get bounced to login.
  46 |     await page.goto("/admin/promotions?section=flash-sales", { waitUntil: "domcontentloaded", timeout: 120_000 });
  47 |     await expect(
  48 |       page.getByRole("heading", { name: /Promotions/i }).first(),
  49 |     ).toBeVisible({ timeout: 30_000 });
  50 | 
  51 |     // Now verify the promotions API prefix resolves to the real backend route
  52 |     // (unauthenticated /admin requests are rejected with 401 before routing).
  53 |     const refresh = await page.request.post("/auth/refresh", { failOnStatusCode: false });
  54 |     const token = refresh.ok() ? (await refresh.json()).access_token : null;
  55 |     const auth = token ? { Authorization: `Bearer ${token}` } : undefined;
  56 | 
  57 |     const good = await page.request.get("/admin/promotions/flash-sales", {
  58 |       headers: auth,
  59 |       failOnStatusCode: false,
  60 |     });
  61 |     expect(good.status()).toBe(200);
  62 |   });
  63 | });
  64 | 
```