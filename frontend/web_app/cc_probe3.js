const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const resp = [];
  page.on("response", (r) => { if (r.status() >= 400) resp.push(r.status() + " " + r.url()); });
  const BASE = "http://localhost:3111";
  await page.goto(BASE + "/admin/login", { waitUntil: "networkidle" });
  await page.fill('input[placeholder="Your username"]', "admin@test.com");
  await page.fill('input[type="password"]', "admin123");
  await page.click('button:has-text("Sign In")');
  await page.waitForTimeout(4000);
  console.log("=== FAILED RESPONSES ===");
  console.log(resp.join("\n"));
  await browser.close();
})();
