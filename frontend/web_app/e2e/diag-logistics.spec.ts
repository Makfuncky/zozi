import { test, type Page, type ConsoleMessage } from "@playwright/test";

test("logistics dashboard deep dive", async ({ page }) => {
  const errors: string[] = [];
  const consoleAll: string[] = [];
  page.on("console", (m: ConsoleMessage) => {
    consoleAll.push(`[${m.type()}] ${m.text()}`);
    if (m.type() === "error") errors.push(m.text());
  });
  page.on("pageerror", (e) => errors.push("PAGEERROR: " + e.message));
  page.on("requestfailed", (r) => errors.push("REQFAIL: " + r.url() + " " + (r.failure()?.errorText || "")));

  // login via form for reliable session
  await page.goto("/logistics-partner/login", { waitUntil: "domcontentloaded", timeout: 60_000 });
  const submit = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await submit.waitFor({ timeout: 30_000 });
  const form = submit.locator("xpath=ancestor::form[1]");
  const id = form.locator("input:not([type='password']):visible").first();
  await id.fill("logistics@zozi.com");
  await form.locator("input[type='password']:visible").first().fill("logistics123");
  await submit.click();
  await page.waitForTimeout(3000);
  console.log("after login url:", page.url());

  const t0 = Date.now();
  let sidebarAttached = false;
  while (Date.now() - t0 < 60_000) {
    const c = await page.locator("aside.theme-sidebar-shell").count();
    if (c > 0) { sidebarAttached = true; break; }
    await page.waitForTimeout(1000);
  }
  console.log("sidebarAttached:", sidebarAttached, "elapsedMs:", Date.now() - t0);

  const h1 = await page.locator("h1").first().textContent().catch(() => "NONE");
  const bodyText = (await page.evaluate(() => document.body.innerText.slice(0, 400))).replace(/\s+/g, " ");
  console.log("h1:", h1);
  console.log("bodyText:", bodyText);
  console.log("ERRORS:", JSON.stringify(errors.slice(0, 12), null, 2));
  console.log("CONSOLE(last12):", JSON.stringify(consoleAll.slice(-12), null, 2));
});
