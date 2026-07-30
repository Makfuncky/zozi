# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth.spec.ts >> Authentication E2E >> displays login form
- Location: e2e\auth.spec.ts:9:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText(/sign in|log in|signin/i).first()
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByText(/sign in|log in|signin/i).first()

```

```yaml
- text: "{\"detail\":\"Method Not Allowed\"}"
```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | import { loginAs } from "../helpers/auth";
  3  | 
  4  | test.describe("Authentication E2E", () => {
  5  |   test.beforeEach(async ({ page }) => {
  6  |     await page.goto("/auth/login", { waitUntil: "domcontentloaded", timeout: 60_000 });
  7  |   });
  8  | 
  9  |   test("displays login form", async ({ page }) => {
> 10 |     await expect(page.getByText(/sign in|log in|signin/i).first()).toBeVisible();
     |                                                                    ^ Error: expect(locator).toBeVisible() failed
  11 |   });
  12 | 
  13 |   test("customer can login", async ({ page }) => {
  14 |     await loginAs(page, "customer@zozi.com", "customer123");
  15 |     await expect(page).toHaveURL(/\/(?:$|\?)/);
  16 |   });
  17 | 
  18 |   test("supplier can login", async ({ page }) => {
  19 |     await loginAs(page, "supplier@zozi.com", "supplier123");
  20 |     await expect(page).toHaveURL(/\/(?:$|\?)/);
  21 |   });
  22 | 
  23 |   test("admin can login", async ({ page }) => {
  24 |     await loginAs(page, "admin@zozi.com", "admin123");
  25 |     await expect(page).toHaveURL(/\/(?:$|\?)/);
  26 |   });
  27 | 
  28 |   test("shows error on wrong password", async ({ page }) => {
  29 |     await page.locator("input[type='email']").first().fill("customer@zozi.com");
  30 |     await page.locator("input[type='password']").first().fill("wrongpassword");
  31 |     await page.getByRole("button", { name: /sign in|log in|signin/i }).first().click();
  32 |     await expect(page.getByText(/invalid credentials|incorrect|error/i).first()).toBeVisible({ timeout: 30_000 });
  33 |   });
  34 | 
  35 |   test("shows error on missing credentials", async ({ page }) => {
  36 |     await page.getByRole("button", { name: /sign in|log in|signin/i }).first().click();
  37 |     await expect(page.getByText(/required|fill/i).first()).toBeVisible({ timeout: 15_000 });
  38 |   });
  39 | });
  40 | 
```