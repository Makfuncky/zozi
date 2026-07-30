# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin-communication-hub.spec.ts >> Admin Communication Hub >> Chat panel: displays threads and supports create flow
- Location: e2e\admin-communication-hub.spec.ts:255:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('tab', { name: /chat/i })

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - link "Skip to main content" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - main [ref=e5]:
    - generic [ref=e6]:
      - img "Zozi logo" [ref=e9]
      - paragraph [ref=e25]: Loading admin...
  - alert [ref=e26]
```

# Test source

```ts
  156 |         total_subscribers: 5000,
  157 |         active_campaigns: 2,
  158 |         total_campaigns: campaigns.length,
  159 |         total_sent: campaigns.reduce((s, c) => s + c.sent_count, 0),
  160 |       });
  161 |     });
  162 | 
  163 |     await page.route("**/admin/email/campaigns/**", async (route) => {
  164 |       if (route.request().method() === "GET") {
  165 |         await fulfillJson(route, campaigns);
  166 |       } else {
  167 |         const body = route.request().postDataJSON();
  168 |         const newCampaign: Campaign = {
  169 |           id: campaigns.length + 1,
  170 |           name: body.name,
  171 |           subject: body.subject,
  172 |           status: "draft",
  173 |           sent_count: 0, opened_count: 0,
  174 |           created_at: new Date().toISOString(),
  175 |           country_code: "AE",
  176 |         };
  177 |         campaigns.push(newCampaign);
  178 |         await fulfillJson(route, newCampaign, 201);
  179 |       }
  180 |     });
  181 | 
  182 |     await page.route("**/admin/chat/threads", async (route) => {
  183 |       if (route.request().method() === "GET") {
  184 |         await fulfillJson(route, threads);
  185 |       } else {
  186 |         const url = new URL(route.request().url());
  187 |         const title = url.searchParams.get("title") || "New Thread";
  188 |         const newThread: Thread = {
  189 |           id: threads.length + 1,
  190 |           title,
  191 |           entity_type: url.searchParams.get("entity_type") || "admin",
  192 |           entity_id: 0,
  193 |           last_message: "",
  194 |           created_at: new Date().toISOString(),
  195 |         };
  196 |         threads.push(newThread);
  197 |         await fulfillJson(route, newThread, 201);
  198 |       }
  199 |     });
  200 | 
  201 |     await page.route("**/admin/chat/metrics", async (route) => {
  202 |       await fulfillJson(route, {
  203 |         total_threads: threads.length,
  204 |         total_messages: 50,
  205 |       });
  206 |     });
  207 | 
  208 |     // Auth + session
  209 |     await mockAdminSession(page);
  210 |   });
  211 | 
  212 |   // ═══════════════ Video Panel ═══════════════
  213 | 
  214 |   test("Video panel: displays rooms and supports create flow", async ({ page }) => {
  215 |     await page.getByRole("tab", { name: /video/i }).click();
  216 |     await page.waitForTimeout(1000);
  217 | 
  218 |     await expect(page.getByText("Secure Video Boardrooms")).toBeVisible();
  219 |     await expect(page.getByRole("button", { name: /create room/i })).toBeVisible();
  220 | 
  221 |     await page.getByRole("button", { name: /create room/i }).click();
  222 |     await expect(page.getByText("New Video Room")).toBeVisible({ timeout: 5000 });
  223 | 
  224 |     await page.getByPlaceholder(/Q3 Board Review/i).fill("E2E Test Room");
  225 |     await page.getByRole("button", { name: /create room/i }).last().click();
  226 |     await page.waitForTimeout(1000);
  227 | 
  228 |     await expect(page.getByText("E2E Test Room")).toBeVisible();
  229 |   });
  230 | 
  231 |   // ═══════════════ Email Panel ═══════════════
  232 | 
  233 |   test("Email panel: overview stats and campaign creation", async ({ page }) => {
  234 |     await page.getByRole("tab", { name: /email/i }).click();
  235 |     await page.waitForTimeout(1000);
  236 | 
  237 |     await expect(page.getByText(/subscribers|Emails Sent|Avg Open Rate/i)).toBeVisible();
  238 | 
  239 |     await page.getByRole("tab", { name: /campaigns/i }).click();
  240 |     await page.waitForTimeout(500);
  241 | 
  242 |     await page.getByRole("button", { name: /new campaign/i }).click();
  243 |     await expect(page.getByText("New Email Campaign")).toBeVisible({ timeout: 5000 });
  244 | 
  245 |     await page.getByPlaceholder(/e\.g\. Summer Sale/i).fill("E2E Campaign");
  246 |     await page.getByPlaceholder(/Don't miss/i).fill("E2E Subject Line");
  247 |     await page.getByRole("button", { name: /create campaign/i }).click();
  248 |     await page.waitForTimeout(1000);
  249 | 
  250 |     await expect(page.getByText("E2E Campaign")).toBeVisible();
  251 |   });
  252 | 
  253 |   // ═══════════════ Chat Panel ═══════════════
  254 | 
  255 |   test("Chat panel: displays threads and supports create flow", async ({ page }) => {
> 256 |     await page.getByRole("tab", { name: /chat/i }).click();
      |                                                    ^ Error: locator.click: Test timeout of 30000ms exceeded.
  257 |     await page.waitForTimeout(1000);
  258 | 
  259 |     await expect(page.getByText(/threads/i)).toBeVisible();
  260 |     await expect(page.getByRole("button", { name: /new/i })).toBeVisible();
  261 | 
  262 |     // Create a thread
  263 |     await page.getByRole("button", { name: /new/i }).click();
  264 |     await expect(page.getByText("New Chat Thread")).toBeVisible({ timeout: 5000 });
  265 | 
  266 |     await page.getByPlaceholder(/Order #1234/i).fill("E2E Thread");
  267 |     await page.getByRole("button", { name: /create thread/i }).click();
  268 |     await page.waitForTimeout(1000);
  269 | 
  270 |     await expect(page.getByText("E2E Thread")).toBeVisible();
  271 |   });
  272 | });
  273 | 
  274 | 
```