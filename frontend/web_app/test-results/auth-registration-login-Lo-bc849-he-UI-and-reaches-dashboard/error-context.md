# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth-registration-login.spec.ts >> Login — UI flow >> admin can login through the UI and reaches dashboard
- Location: e2e\auth-registration-login.spec.ts:290:7

# Error details

```
Test timeout of 120000ms exceeded.
```

```
Error: locator.fill: Test timeout of 120000ms exceeded.
Call log:
  - waiting for locator('input[type=\'email\'], input[name=\'username\'], input[name=\'email\'], input[autocomplete=\'username\']').first()

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - main [ref=e5]:
    - generic [ref=e6]:
      - generic [ref=e7]:
        - heading "Admin Access" [level=1] [ref=e11]
        - paragraph [ref=e12]: Restricted area. Staff credentials required.
      - generic [ref=e13]:
        - generic [ref=e14]:
          - generic [ref=e15]: Username
          - textbox "Your username" [ref=e16]
        - generic [ref=e17]:
          - generic [ref=e18]: Password
          - textbox "••••••••" [ref=e19]
        - button "Sign In" [ref=e20]
  - alert [ref=e24]
```

# Test source

```ts
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
  302 |       )
  303 |       .first();
> 304 |     await identifierInput.fill("admin@zozi.com");
      |                           ^ Error: locator.fill: Test timeout of 120000ms exceeded.
  305 | 
  306 |     const passwordInput = page.locator("input[type='password']").first();
  307 |     const adminPassword = process.env.SEED_ADMIN_PASSWORD || process.env.E2E_ADMIN_PASSWORD || "DevSeed123!";
  308 |     await passwordInput.fill(adminPassword);
  309 | 
  310 |     // Submit
  311 |     const submitBtn = page
  312 |       .getByRole("button", { name: /sign in|log in|signin/i })
  313 |       .first();
  314 |     await submitBtn.click();
  315 | 
  316 |     // Wait for navigation away from login
  317 |     await page.waitForTimeout(5000);
  318 |     const url = page.url();
  319 |     const loggedIn =
  320 |       url.includes("admin/dashboard") ||
  321 |       url.includes("admin/command-center") ||
  322 |       url.includes("admin") && !url.includes("login");
  323 |     expect(loggedIn).toBe(true);
  324 |   });
  325 | 
  326 |   test("customer can login through the UI and reaches products", async ({
  327 |     page,
  328 |   }) => {
  329 |     // First register a fresh customer
  330 |     const email = uniqueEmail("cust_login_ui");
  331 |     const username = uniqueUsername("cust_login_ui");
  332 |     await registerUser(page, {
  333 |       email,
  334 |       username,
  335 |       password: TEST_PASSWORD,
  336 |       role: "customer",
  337 |     });
  338 | 
  339 |     // Now login via UI
  340 |     await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  341 |     await page.waitForLoadState("networkidle").catch(() => {});
  342 | 
  343 |     const identifierInput = page
  344 |       .locator(
  345 |         "input[type='email'], input[name='username'], input[name='email'], input[autocomplete='username']"
  346 |       )
  347 |       .first();
  348 |     await identifierInput.fill(email);
  349 | 
  350 |     const passwordInput = page.locator("input[type='password']").first();
  351 |     await passwordInput.fill(TEST_PASSWORD);
  352 | 
  353 |     const submitBtn = page
  354 |       .getByRole("button", { name: /sign in|log in|signin/i })
  355 |       .first();
  356 |     await submitBtn.click();
  357 | 
  358 |     await page.waitForTimeout(5000);
  359 |     const url = page.url();
  360 |     const loggedIn =
  361 |       url.includes("products") ||
  362 |       url.includes("dashboard") ||
  363 |       url.includes("orders") ||
  364 |       !url.includes("login");
  365 |     expect(loggedIn).toBe(true);
  366 |   });
  367 | });
  368 | 
  369 | test.describe("Database persistence verification", () => {
  370 |   test("registered user survives server restart (token validity)", async ({
  371 |     page,
  372 |   }) => {
  373 |     const email = uniqueEmail("persist");
  374 |     const username = uniqueUsername("persist");
  375 | 
  376 |     // Register
  377 |     const regResult = await registerUser(page, {
  378 |       email,
  379 |       username,
  380 |       password: TEST_PASSWORD,
  381 |       role: "customer",
  382 |     });
  383 |     expect(regResult.status).toBe(200);
  384 | 
  385 |     // Login
  386 |     const loginResult = await loginUser(page, email, TEST_PASSWORD);
  387 |     expect(loginResult.status).toBe(200);
  388 |     const token = loginResult.body.access_token as string;
  389 |     expect(token).toBeDefined();
  390 | 
  391 |     // Verify token works (user persisted in DB)
  392 |     const meResult = await verifyUser(page, token);
  393 |     expect(meResult.status).toBe(200);
  394 |     expect(meResult.body.email).toBe(email);
  395 | 
  396 |     // Create a new page context (simulate fresh session) and verify token still works
  397 |     const freshContext = await page.context().browser()!.newContext();
  398 |     const freshPage = await freshContext.newPage();
  399 |     const freshResult = await verifyUser(freshPage, token as string);
  400 |     expect(freshResult.status).toBe(200);
  401 |     expect(freshResult.body.email).toBe(email);
  402 |     await freshContext.close();
  403 |   });
  404 | 
```