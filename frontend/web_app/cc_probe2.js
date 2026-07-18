const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const BASE = "http://localhost:3111";
  await page.goto(BASE + "/admin/login", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  const html = await page.evaluate(() => {
    const inputs = [...document.querySelectorAll("input")].map(i => i.type + "|" + (i.name||"") + "|" + (i.id||"") + "|ph=" + (i.placeholder||""));
    return { url: location.href, text: document.body.innerText.slice(0,400), inputs };
  });
  console.log(JSON.stringify(html, null, 2));
  await browser.close();
})();
