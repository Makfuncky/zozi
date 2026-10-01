# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth-registration-login.spec.ts >> Registration — all roles (API) >> customer registration persists to database
- Location: e2e\auth-registration-login.spec.ts:118:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 200
Received: 403
```

# Test source

```ts
  29  |   email: string,
  30  |   username: string,
  31  |   password: string,
  32  |   opts?: { business_name?: string }
  33  | ) {
  34  |   const registerUrl =
  35  |     role === "customer"
  36  |       ? "/register"
  37  |       : role === "supplier"
  38  |         ? "/supplier/register"
  39  |         : role === "logistics_partner"
  40  |           ? "/logistics-partner/register"
  41  |           : "/register";
  42  | 
  43  |   await page.goto(`${BASE}${registerUrl}`, { waitUntil: "domcontentloaded" });
  44  |   await page.waitForLoadState("networkidle").catch(() => {});
  45  | 
  46  |   // Fill email
  47  |   const emailInput = page
  48  |     .locator(
  49  |       "input[type='email'], input[name='email'], input[autocomplete='email']"
  50  |     )
  51  |     .first();
  52  |   if (await emailInput.isVisible()) {
  53  |     await emailInput.fill(email);
  54  |   }
  55  | 
  56  |   // Fill username
  57  |   const usernameInput = page
  58  |     .locator(
  59  |       "input[name='username'], input[autocomplete='username'], input[placeholder*='user' i]"
  60  |     )
  61  |     .first();
  62  |   if (await usernameInput.isVisible()) {
  63  |     await usernameInput.fill(username);
  64  |   }
  65  | 
  66  |   // Fill business name if supplier
  67  |   if (opts?.business_name) {
  68  |     const bizInput = page
  69  |       .locator(
  70  |         "input[name='business_name'], input[placeholder*='business' i], input[placeholder*='company' i]"
  71  |       )
  72  |       .first();
  73  |     if (await bizInput.isVisible()) {
  74  |       await bizInput.fill(opts.business_name);
  75  |     }
  76  |   }
  77  | 
  78  |   // Fill password
  79  |   const passwordInput = page.locator("input[type='password']").first();
  80  |   if (await passwordInput.isVisible()) {
  81  |     await passwordInput.fill(password);
  82  |   }
  83  | 
  84  |   // Fill confirm password if present
  85  |   const confirmInput = page.locator("input[type='password']").nth(1);
  86  |   if ((await confirmInput.count()) > 0 && (await confirmInput.isVisible())) {
  87  |     await confirmInput.fill(password);
  88  |   }
  89  | 
  90  |   // Accept terms checkbox if present
  91  |   const termsCheckbox = page
  92  |     .locator("input[type='checkbox']")
  93  |     .first();
  94  |   if (
  95  |     (await termsCheckbox.count()) > 0 &&
  96  |     (await termsCheckbox.isVisible()) &&
  97  |     !(await termsCheckbox.isChecked())
  98  |   ) {
  99  |     await termsCheckbox.check();
  100 |   }
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
> 129 |     expect(result.status).toBe(200);
      |                           ^ Error: expect(received).toBe(expected) // Object.is equality
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
```