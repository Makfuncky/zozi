import { test, type Page } from "@playwright/test";

async function getW(page: Page) {
  return page.evaluate(() => {
    const el = document.querySelector("aside.theme-sidebar-shell") as HTMLElement | null;
    return el ? Math.round(el.getBoundingClientRect().width) : -1;
  });
}

async function loginForm(page: Page, loginPath: string, user: string, pass: string) {
  await page.goto(loginPath, { waitUntil: "domcontentloaded", timeout: 60_000 });
  const submit = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await submit.waitFor({ state: "visible", timeout: 60_000 });
  const form = submit.locator("xpath=ancestor::form[1]");
  const id = form.locator("input:not([type='password']):visible").first();
  await id.fill(user);
  await form.locator("input[type='password']:visible").first().fill(pass);
  await submit.click();
  // wait until we leave the login page (session established)
  await page.waitForURL(/\/(admin|supplier|logistics-partner)\/dashboard/, { timeout: 60_000 });
}

test("confirm admin sidebar collapses (reliable form login)", async ({ page }) => {
  await page.setViewportSize({ width: 1366, height: 900 });
  await loginForm(page, "/admin/login", "admin@zozi.com", "admin123");
  await page.waitForSelector("aside.theme-sidebar-shell", { state: "attached", timeout: 60_000 });
  await page.waitForLoadState("networkidle", { timeout: 30_000 }).catch(() => {});
  await page.waitForTimeout(1500);

  const before = await getW(page);
  await page.getByRole("button", { name: /collapse sidebar/i }).first().click();
  const series: number[] = [];
  for (let i = 0; i < 10; i++) {
    await page.waitForTimeout(300);
    series.push(await getW(page));
  }
  console.log("before=", before, "series=", JSON.stringify(series));
  await page.screenshot({ path: "test-results/collapse-confirm.png" });
});
