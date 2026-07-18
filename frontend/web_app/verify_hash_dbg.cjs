const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const base = "http://127.0.0.1:3000";

  await page.goto(base + "/products/14c64d24", { waitUntil: "networkidle" });
  await page.waitForTimeout(2500);
  const title = await page.title();
  const body = await page.locator("body").innerText();
  console.log("TITLE:", title);
  console.log("BODY(first 400):", body.replace(/\s+/g, " ").slice(0, 400));
  console.log("contains Silk?", /Silk Scarf/.test(body));
  console.log("contains Bottle?", /Bottle/.test(body));

  await browser.close();
})();
