# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth-registration-login.spec.ts >> Registration — all roles (API) >> duplicate email registration is rejected
- Location: e2e\auth-registration-login.spec.ts:191:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 200
Received: 403
```

# Test source

```ts
  101 | 
  102 |   // Submit
  103 |   const submitBtn = page
  104 |     .getByRole("button", {
  105 |       name: /register|sign up|create.*account/i,
  106 |     })
  107 |     .first();
  108 |   if (await submitBtn.isVisible()) {
  109 |     await submitBtn.click();
  110 |   }
  111 | }
  112 | 
  113 | // ── Tests ────────────────────────────────────────────────────────────────────
  114 | 
  115 | test.describe.configure({ timeout: 120_000 });
  116 | 
  117 | test.describe("Registration — all roles (API)", () => {
  118 |   test("customer registration persists to database", async ({ page }) => {
  119 |     const email = uniqueEmail("customer");
  120 |     const username = uniqueUsername("customer");
  121 | 
  122 |     const result = await registerUser(page, {
  123 |       email,
  124 |       username,
  125 |       password: TEST_PASSWORD,
  126 |       role: "customer",
  127 |     });
  128 | 
  129 |     expect(result.status).toBe(200);
  130 |     expect(result.body).toHaveProperty("id");
  131 |     expect(result.body.email).toBe(email);
  132 |     expect(result.body.role).toBe("customer");
  133 | 
  134 |     // Verify persistence: login and query /me
  135 |     const loginResult = await loginUser(page, email, TEST_PASSWORD);
  136 |     expect(loginResult.status).toBe(200);
  137 |     expect(loginResult.body).toHaveProperty("access_token");
  138 | 
  139 |     const token = loginResult.body.access_token!;
  140 |     const meResult = await verifyUser(page, token);
  141 |     expect(meResult.status).toBe(200);
  142 |     expect(meResult.body.email).toBe(email);
  143 |     expect(meResult.body.role).toBe("customer");
  144 |   });
  145 | 
  146 |   test("supplier registration persists with business profile", async ({
  147 |     page,
  148 |   }) => {
  149 |     const email = uniqueEmail("supplier");
  150 |     const username = uniqueUsername("supplier");
  151 | 
  152 |     const result = await registerUser(page, {
  153 |       email,
  154 |       username,
  155 |       password: TEST_PASSWORD,
  156 |       role: "supplier",
  157 |       business_name: "E2E Test Supplier Co",
  158 |     });
  159 | 
  160 |     expect(result.status).toBe(200);
  161 |     expect(result.body).toHaveProperty("id");
  162 |     expect(result.body.role).toBe("supplier");
  163 | 
  164 |     // Verify login works
  165 |     const loginResult = await loginUser(page, email, TEST_PASSWORD);
  166 |     expect(loginResult.status).toBe(200);
  167 |   });
  168 | 
  169 |   test("logistics_partner registration persists with partner profile", async ({
  170 |     page,
  171 |   }) => {
  172 |     const email = uniqueEmail("logistics");
  173 |     const username = uniqueUsername("logistics");
  174 | 
  175 |     const result = await registerUser(page, {
  176 |       email,
  177 |       username,
  178 |       password: TEST_PASSWORD,
  179 |       role: "logistics_partner",
  180 |     });
  181 | 
  182 |     expect(result.status).toBe(200);
  183 |     expect(result.body).toHaveProperty("id");
  184 |     expect(result.body.role).toBe("logistics_partner");
  185 | 
  186 |     // Verify login works
  187 |     const loginResult = await loginUser(page, email, TEST_PASSWORD);
  188 |     expect(loginResult.status).toBe(200);
  189 |   });
  190 | 
  191 |   test("duplicate email registration is rejected", async ({ page }) => {
  192 |     const email = uniqueEmail("dup_test");
  193 | 
  194 |     // First registration succeeds
  195 |     const first = await registerUser(page, {
  196 |       email,
  197 |       username: uniqueUsername("dup1"),
  198 |       password: TEST_PASSWORD,
  199 |       role: "customer",
  200 |     });
> 201 |     expect(first.status).toBe(200);
      |                          ^ Error: expect(received).toBe(expected) // Object.is equality
  202 | 
  203 |     // Second registration with same email fails
  204 |     const second = await registerUser(page, {
  205 |       email,
  206 |       username: uniqueUsername("dup2"),
  207 |       password: TEST_PASSWORD,
  208 |       role: "customer",
  209 |     });
  210 |     expect(second.status).toBe(400);
  211 |     expect(second.body.detail).toMatch(/already registered/i);
  212 |   });
  213 | 
  214 |   test("weak password is rejected", async ({ page }) => {
  215 |     const result = await registerUser(page, {
  216 |       email: uniqueEmail("weak"),
  217 |       username: uniqueUsername("weak"),
  218 |       password: "weak",
  219 |       role: "customer",
  220 |     });
  221 |     expect(result.status).toBe(422);
  222 |     expect(result.body.detail).toMatch(/password/i);
  223 |   });
  224 | });
  225 | 
  226 | test.describe("Login — all roles (API)", () => {
  227 |   test("admin login returns valid token with correct role", async ({ page }) => {
  228 |     // First ensure the admin user exists (seeded by backend)
  229 |     const adminPassword = process.env.SEED_ADMIN_PASSWORD || process.env.E2E_ADMIN_PASSWORD || "DevSeed123!";
  230 |     const result = await loginUser(page, "admin@zozi.com", adminPassword);
  231 | 
  232 |     if (result.status !== 200) {
  233 |       const altResult = await loginUser(page, "admin@zozi.com", "Admin@123");
  234 |       expect(altResult.status).toBe(200);
  235 |       expect(altResult.body).toHaveProperty("access_token");
  236 |       return;
  237 |     }
  238 | 
  239 |     expect(result.status).toBe(200);
  240 |     expect(result.body).toHaveProperty("access_token");
  241 |     expect(result.body).toHaveProperty("refresh_token");
  242 | 
  243 |     // Verify the token resolves to correct user
  244 |     const meResult = await verifyUser(page, result.body.access_token!);
  245 |     expect(meResult.status).toBe(200);
  246 |     expect(meResult.body.role).toBe("admin");
  247 |   });
  248 | 
  249 |   test("wrong password returns 400", async ({ page }) => {
  250 |     const result = await loginUser(
  251 |       page,
  252 |       "admin@zozi.com",
  253 |       "WrongPassword123!"
  254 |     );
  255 |     expect(result.status).toBe(400);
  256 |     expect(result.body.detail).toMatch(/incorrect/i);
  257 |   });
  258 | 
  259 |   test("nonexistent user returns 400", async ({ page }) => {
  260 |     const result = await loginUser(
  261 |       page,
  262 |       "nonexistent@zozi-test.com",
  263 |       "AnyPass123!"
  264 |     );
  265 |     expect(result.status).toBe(400);
  266 |   });
  267 | });
  268 | 
  269 | test.describe("Registration — UI flow", () => {
  270 |   test("customer can register through the UI form", async ({ page }) => {
  271 |     const email = uniqueEmail("customer_ui");
  272 |     const username = uniqueUsername("customer_ui");
  273 | 
  274 |     await registerViaUI(page, "customer", email, username, TEST_PASSWORD);
  275 | 
  276 |     // After registration, should redirect or show success
  277 |     await page.waitForTimeout(3000);
  278 |     const url = page.url();
  279 |     const successOrRedirect =
  280 |       url.includes("login") ||
  281 |       url.includes("verify") ||
  282 |       url.includes("dashboard") ||
  283 |       url.includes("products") ||
  284 |       (await page.getByText(/success|verify|welcome/i).count()) > 0;
  285 |     expect(successOrRedirect).toBe(true);
  286 |   });
  287 | });
  288 | 
  289 | test.describe("Login — UI flow", () => {
  290 |   test("admin can login through the UI and reaches dashboard", async ({
  291 |     page,
  292 |   }) => {
  293 |     await page.goto(`${BASE}/admin/login`, {
  294 |       waitUntil: "domcontentloaded",
  295 |     });
  296 |     await page.waitForLoadState("networkidle").catch(() => {});
  297 | 
  298 |     // Fill credentials
  299 |     const identifierInput = page
  300 |       .locator(
  301 |         "input[type='email'], input[name='username'], input[name='email'], input[autocomplete='username']"
```