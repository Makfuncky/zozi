const { chromium } = require("playwright");
const BASE = "http://localhost:3000";
async function captureLoginToken(page) {
  return new Promise((resolve) => {
    const h = async (r) => { if (r.url().endsWith("/auth/login")) { try { const b = await r.json(); if (b && b.access_token) { page.off("response", h); resolve(b.access_token); } } catch {} } };
    page.on("response", h);
  });
}
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on("response", (r) => { const u = r.url(); if ((u.includes("/__api/") || u.includes("/auth/")) && r.status() >= 400) console.log("NET>=400", r.status(), u.replace(BASE, "")); });
  const tok = captureLoginToken(page);
  await page.goto(BASE + "/login", { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("load");
  const form = page.locator('form:has(input[type="password"])');
  await form.locator('input[placeholder="you@email.com"]').pressSequentially("customer@test.com", { delay: 15 });
  await form.locator('input[type="password"]').pressSequentially("customer123", { delay: 15 });
  await form.locator('button[type="submit"]:not([disabled])').click();
  await tok;
  console.log("logged in (token captured)");
  await page.waitForTimeout(2500);
  console.log("post-login url:", page.url());
  const sess = await page.evaluate(() => ({ has: localStorage.getItem("zozi_has_session"), body: document.body.innerText.slice(0, 120) }));
  console.log("has_session:", sess.has, "| body:", sess.body.replace(/\s+/g, " "));
  await page.goto(BASE + "/checkout", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(9000);
  const sess2 = await page.evaluate(() => ({ has: localStorage.getItem("zozi_has_session"), body: document.body.innerText.slice(0, 120) }));
  console.log("checkout has_session:", sess2.has, "| body:", sess2.body.replace(/\s+/g, " "));
  const info = await page.evaluate(async () => {
    let m = "n/a";
    try { const r = await fetch("/__api/payments/methods", { credentials: "include" }); const t = await r.text(); m = r.status + " :: " + t.slice(0, 250); } catch (e) { m = "ERR " + e.message; }
    return { methodsFetch: m, bodyHasPaymob: /paymob/i.test(document.body.innerText), bodyHasPayment: /payment method/i.test(document.body.innerText), bodyLen: document.body.innerText.length };
  });
  console.log("METHODS FETCH:", info.methodsFetch);
  console.log("BODY has paymob:", info.bodyHasPaymob, "| has 'payment method':", info.bodyHasPayment, "| len:", info.bodyLen);
  console.log("BODY:", (await page.textContent("body")).replace(/\s+/g, " ").slice(0, 500));
  await browser.close();
})();
