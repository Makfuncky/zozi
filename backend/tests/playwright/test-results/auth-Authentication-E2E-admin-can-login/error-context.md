# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth.spec.ts >> Authentication E2E >> admin can login
- Location: e2e\auth.spec.ts:23:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: true
Received: false
```

# Page snapshot

```yaml
- generic [active] [ref=e1]: "{\"detail\":\"Method Not Allowed\"}"
```

# Test source

```ts
  1  | import { expect, type Page } from "@playwright/test";
  2  | 
  3  | export async function loginAs(page: Page, email: string, password: string): Promise<void> {
  4  |   const token = await apiLogin(page, email, password);
  5  |   await page.route("**/*", async (route) => {
  6  |     const headers = { ...route.request().headers() };
  7  |     if (!headers["authorization"]) {
  8  |       headers["authorization"] = `Bearer ${token}`;
  9  |     }
  10 |     route.continue({ headers });
  11 |   });
  12 |   await page.goto("/", { waitUntil: "domcontentloaded", timeout: 60_000 });
  13 | }
  14 | 
  15 | export async function expectApiJson(page: Page, url: string, expectedStatus: number) {
  16 |   const resp = await page.request.get(url);
  17 |   expect(resp.status()).toBe(expectedStatus);
  18 |   return await resp.json();
  19 | }
  20 | 
  21 | export async function apiLogin(page: Page, email: string, password: string) {
  22 |   const resp = await page.request.post("/auth/login", {
  23 |     json: { username: email, password },
  24 |     failOnStatusCode: false,
  25 |   });
> 26 |   expect(resp.ok()).toBe(true);
     |                     ^ Error: expect(received).toBe(expected) // Object.is equality
  27 |   const data = await resp.json();
  28 |   return data.access_token as string;
  29 | }
  30 | 
```