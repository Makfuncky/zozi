const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push("console:" + m.text()); });
  page.on("requestfailed", (r) => {
    const u = r.url();
    if (u.includes("/__api/") || u.includes("/products/")) errors.push("reqfail:" + u + " " + (r.failure()?.errorText || ""));
  });

  const base = "http://127.0.0.1:3000";

  // Navigate ONLY to the hash URL
  await page.goto(base + "/products/14c64d24", { waitUntil: "networkidle" });
  await page.waitForSelector("text=/Silk Scarf/i", { timeout: 15000 }).catch(() => {});
  const body = await page.locator("body").innerText();
  const showsProduct = /Silk Scarf/.test(body);
  const title = await page.title();
  console.log(`[hash-only] title=${title} showsProduct=${showsProduct} errors=${errors.length}`);
  if (errors.length) console.log("  errors:", errors.slice(0, 6));

  console.log("DONE");
  await browser.close();
})();
