const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on("response", (r) => { if (r.status() >= 400) console.log("NET>=400", r.status(), r.url()); });
  page.on("requestfailed", (r) => console.log("REQFAIL", r.url(), r.failure() && r.failure().errorText));
  page.on("console", (m) => { if (/error|exception|boundary/i.test(m.text())) console.log("CONSOLE", m.text().slice(0, 300)); });
  await page.goto("http://localhost:3000/admin/login", { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  console.log("URL:", page.url());
  const html = await page.content();
  const inputs = await page.$$eval("input", (els) => els.map((e) => e.type + (e.type === "password" ? "" : "") + " name=" + (e.name || "") + " id=" + (e.id || "")));
  console.log("INPUTS:", JSON.stringify(inputs));
  console.log("HAS username input:", /username/i.test(html));
  console.log("BODY SNIPPET:", html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").slice(0, 600));
  await browser.close();
})();
