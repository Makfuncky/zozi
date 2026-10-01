# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth-registration-login.spec.ts >> Registration — UI flow >> customer can register through the UI form
- Location: e2e\auth-registration-login.spec.ts:270:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: true
Received: false
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - banner [ref=e4]:
      - generic [ref=e5]:
        - generic [ref=e6]:
          - link "Go to home" [ref=e7] [cursor=pointer]:
            - /url: /
            - generic [ref=e8]:
              - img "Zozi logo" [ref=e10]
              - generic [ref=e26]: Zozi
          - generic [ref=e30]:
            - button "All Products" [ref=e32]
            - button "Price" [ref=e40]
            - button "Rating" [ref=e48]
            - button "Supplier" [ref=e55]
            - textbox "Search products, brands, suppliers..." [ref=e64]
            - button "Search by image" [ref=e65]
            - button "Voice search" [ref=e69]
            - button "Search" [ref=e73]
          - generic [ref=e78]:
            - button "Switch to dark theme" [ref=e79]: 🌙
            - generic [ref=e80]:
              - generic [ref=e81]:
                - generic [ref=e82]: OMR
                - generic [ref=e83]: Auto detected
              - button "Choose country" [ref=e85]:
                - generic [ref=e86]: AUTO
              - button "Choose language" [ref=e90]:
                - generic [ref=e91]: EN
            - link "Wishlist" [ref=e94] [cursor=pointer]:
              - /url: /wishlist
            - link "Cart" [ref=e97] [cursor=pointer]:
              - /url: /cart
            - button "Open sign in menu" [ref=e102]
        - navigation [ref=e106]:
          - generic [ref=e107]:
            - link "Shop" [ref=e108] [cursor=pointer]:
              - /url: /products
            - link "Suppliers" [ref=e109] [cursor=pointer]:
              - /url: /suppliers
            - link "Offers" [ref=e110] [cursor=pointer]:
              - /url: /offers
            - link "Help" [ref=e111] [cursor=pointer]:
              - /url: /help
    - main [ref=e114]:
      - generic [ref=e115]:
        - button "Back to sign in" [ref=e116]
        - generic [ref=e119]:
          - heading "Create your account" [level=1] [ref=e124]
          - paragraph [ref=e125]: Join ZOZI to start shopping
        - generic [ref=e126]:
          - generic [ref=e127]:
            - generic [ref=e128]: Username
            - textbox "username" [ref=e130]: e2e_customer_ui_1790818117357
          - generic [ref=e131]:
            - generic [ref=e132]: Full Name
            - textbox "Your name" [ref=e133]
          - generic [ref=e134]:
            - generic [ref=e135]: Email
            - textbox "you@email.com" [ref=e137]: e2e_customer_ui_1790818117357@zozi-test.com
          - generic [ref=e138]:
            - generic [ref=e139]:
              - generic [ref=e140]: Password
              - textbox "••••••••" [ref=e142]: TestPass123!
              - paragraph [ref=e143]: Min. 8 chars, with uppercase, lowercase, number & special character.
            - generic [ref=e144]:
              - generic [ref=e145]: Confirm
              - textbox "••••••••" [ref=e147]: TestPass123!
          - button "Create Account" [ref=e148]
        - paragraph [ref=e152]:
          - text: Already have an account?
          - link "Sign in" [ref=e153] [cursor=pointer]:
            - /url: /login
    - contentinfo [ref=e155]:
      - generic [ref=e157]:
        - generic [ref=e158]:
          - generic [ref=e159]: ZOZI
          - paragraph [ref=e165]: Trust delivered through verified suppliers, exceptional products, and global reach.
          - generic [ref=e166]:
            - link "Become a Supplier" [ref=e167] [cursor=pointer]:
              - /url: /supplier/register
            - link "Become Logistics Partner" [ref=e168] [cursor=pointer]:
              - /url: /logistics-partner/login
        - generic [ref=e169]:
          - heading "The ZOZI Dispatch" [level=5] [ref=e170]
          - generic [ref=e171]:
            - generic [ref=e172]:
              - heading "Stay in Style" [level=3] [ref=e173]
              - paragraph [ref=e174]: Get exclusive access to new arrivals, special offers, and fashion tips.
            - generic [ref=e175]:
              - textbox "First name (optional)" [ref=e177]
              - textbox "Enter your email" [ref=e179]
              - button "Subscribe" [disabled] [ref=e180]
      - generic [ref=e185]:
        - paragraph [ref=e186]: © 2026 ZOZI. All rights reserved.
        - generic [ref=e187]:
          - link "Terms" [ref=e188] [cursor=pointer]:
            - /url: /terms
          - link "Privacy" [ref=e189] [cursor=pointer]:
            - /url: /privacy
          - link "Cookies" [ref=e190] [cursor=pointer]:
            - /url: /cookies
          - link "Admin Portal" [ref=e191] [cursor=pointer]:
            - /url: /admin/login
    - button "Chat" [ref=e194]
    - generic [ref=e199]:
      - paragraph [ref=e202]: An unexpected error occurred
      - button [ref=e203]
  - alert [ref=e207]
```

# Test source

```ts
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
  201 |     expect(first.status).toBe(200);
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
> 285 |     expect(successOrRedirect).toBe(true);
      |                               ^ Error: expect(received).toBe(expected) // Object.is equality
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
  304 |     await identifierInput.fill("admin@zozi.com");
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
```