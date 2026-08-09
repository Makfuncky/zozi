import { test, type Page, type ConsoleMessage } from "@playwright/test";

const cases = [
  { name: "admin", url: "/admin/dashboard", user: "admin@zozi.com", pass: "admin123", login: "/admin/login" },
  { name: "supplier", url: "/supplier/dashboard", user: "supplier@zozi.com", pass: "supplier123", login: "/supplier/login" },
  { name: "logistics", url: "/logistics-partner/dashboard", user: "logistics@zozi.com", pass: "logistics123", login: "/logistics-partner/login" },
];

for (const c of cases) {
  test(`perf+behavior ${c.name}`, async ({ page }) => {
    const errors: string[] = [];
    const warnings: string[] = [];
    page.on("console", (m: ConsoleMessage) => {
      if (m.type() === "error") errors.push(m.text());
      if (m.type() === "warning") warnings.push(m.text());
    });
    page.on("pageerror", (e) => errors.push("PAGEERROR: " + e.message));

    const t0 = Date.now();
    await page.goto(c.url, { waitUntil: "domcontentloaded", timeout: 60_000 });
    // wait for sidebar
    await page.waitForSelector("aside.theme-sidebar-shell", { state: "attached", timeout: 90_000 });
    const tSidebar = Date.now() - t0;

    // wait for first contentful paint-ish: an h1 in the topbar
    await page.waitForSelector("h1", { timeout: 30_000 });
    const tH1 = Date.now() - t0;

    // Is the global storefront header still present?
    const globalHeader = await page.locator('[data-app-header] > header').count();

    // What element is actually on top of the collapse button? (overlay interception check)
    const collapseBtn = page.getByRole("button", { name: /collapse sidebar/i }).first();
    let topEl = "n/a";
    if (await collapseBtn.count()) {
      topEl = await collapseBtn.evaluate((el) => {
        const r = (el as HTMLElement).getBoundingClientRect();
        const cx = r.left + r.width / 2;
        const cy = r.top + r.height / 2;
        const hit = document.elementFromPoint(cx, cy) as HTMLElement | null;
        if (!hit) return "none";
        if (hit === el || hit.contains(el) || (el as HTMLElement).contains(hit)) return "self";
        return `${hit.tagName}.${(hit.className || "").toString().slice(0, 60)}`;
      });
    }

    // Try clicking collapse, measure width delta + duration
    const wBefore = await page.evaluate(() => Math.round((document.querySelector("aside.theme-sidebar-shell") as HTMLElement).getBoundingClientRect().width));
    const clickStart = Date.now();
    let clickErr = "";
    try {
      await collapseBtn.click({ timeout: 10_000 });
    } catch (e) {
      clickErr = String(e).slice(0, 120);
    }
    await page.waitForTimeout(900);
    const wAfter = await page.evaluate(() => Math.round((document.querySelector("aside.theme-sidebar-shell") as HTMLElement).getBoundingClientRect().width));
    const clickDur = Date.now() - clickStart;

    console.log(JSON.stringify({
      name: c.name,
      tSidebarMs: tSidebar,
      tH1Ms: tH1,
      globalHeader,
      collapseTopElement: topEl,
      wBefore,
      wAfter,
      collapsed: wAfter < wBefore - 30,
      clickDurMs: clickDur,
      clickErr,
      errors: errors.slice(0, 8),
      warnings: warnings.slice(0, 4),
    }, null, 2));
  });
}
