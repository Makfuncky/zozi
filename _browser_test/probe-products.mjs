/**
 * Probe: what does /products actually receive and render?
 * Run: node probe-products.mjs
 */
import { chromium } from "@playwright/test";

const WEB = process.env.WEB_BASE_URL || "http://localhost:3000";
const API = process.env.API_BASE_URL || "http://127.0.0.1:8000";

const login = await fetch(`${API}/api/v1/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username: "customer@zozi.com", password: "E2eCustomer#2026" }),
});
const { access_token } = await login.json();

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
await ctx.addCookies([
  { name: "access_token", value: access_token, domain: "127.0.0.1", path: "/" },
]);
const page = await ctx.newPage();

const apiCalls = [];
page.on("request", (r) => {
  const u = new URL(r.url());
  if (/\/__api\/|\/api\//.test(u.pathname)) apiCalls.push(`--> ${u.pathname}${u.search.slice(0, 50)}`);
});
page.on("response", async (r) => {
  const u = new URL(r.url());
  if (!/\/__api\/|\/api\//.test(u.pathname)) return;
  let summary = "";
  try {
    const d = await r.json();
    if (Array.isArray(d)) summary = `array(${d.length})`;
    else if (d && typeof d === "object") {
      const keys = Object.keys(d);
      const arrKey = keys.find((k) => Array.isArray(d[k]));
      summary = arrKey ? `{${arrKey}: ${d[arrKey].length}} keys=${keys.slice(0, 6)}` : `keys=${keys.slice(0, 8)}`;
    }
  } catch { summary = "(non-json)"; }
  apiCalls.push(`${r.status()} ${u.pathname}${u.search.slice(0, 40)}  ${summary}`);
});

console.log("â†’ goto /products");
await page.goto(`${WEB}/products`, { waitUntil: "domcontentloaded", timeout: 90_000 });
await page.waitForLoadState("networkidle", { timeout: 60_000 }).catch(() => {});
await page.waitForTimeout(25_000);

const dom = await page.evaluate(() => {
  const count = (sel) => document.querySelectorAll(sel).length;
  return {
    productLinks: count('a[href*="/products/"]'),
    testidCards: count('[data-testid*="product"]'),
    articles: count("article"),
    gridChildren: count('[class*="grid"] > *'),
    imgs: count("img"),
    total: count("*"),
    bodyText: (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 400),
  };
});

console.log("\n=== API calls seen by the browser ===");
apiCalls.forEach((c) => console.log("  " + c));
console.log("\n=== DOM ===");
for (const [k, v] of Object.entries(dom)) console.log(`  ${k}: ${typeof v === "number" ? v : v}`);
console.log("\nurl:", page.url());

await page.screenshot({ path: "probe-products.png", fullPage: true });
console.log("saved probe-products.png");
await browser.close();