import { test } from "@playwright/test";

test("debug price filter open", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push("PAGEERR: " + e.message));
  await page.goto("/products", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);
  const btn = page.getByRole("button", { name: "Price filter" });
  console.log("PRICE_FILTER_BTN_COUNT:", await btn.count());
  if (await btn.count() > 0) {
    const exp = await btn.first().getAttribute("aria-expanded");
    console.log("ARIA_EXPANDED_BEFORE:", exp);
    await btn.first().click();
    await page.waitForTimeout(1500);
    console.log("ARIA_EXPANDED_AFTER:", await btn.first().getAttribute("aria-expanded"));
  }
  console.log("THEME_RANGE_DUAL_COUNT:", await page.locator(".theme-range-dual").count());
  console.log("PAGE_ERRORS:", JSON.stringify(errors.slice(0, 5)));
});
