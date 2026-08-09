import { expect, test } from "@playwright/test";

test("debug6 - wait for React hydration", async ({ page }) => {
  const loginRes = await page.request.post("http://localhost:8000/auth/login", {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    form: { username: "supplier@zozi.com", password: "supplier123" },
  });
  const loginData = await loginRes.json();
  const token = loginData.access_token;
  await page.goto("/supplier/products/add", { waitUntil: "domcontentloaded", timeout: 60_000 });
  await page.context().addCookies([{ name: "access_token", value: token, url: "http://localhost:3000" }]);
  await page.evaluate((t) => { localStorage.setItem("access_token", t); localStorage.setItem("zozi_has_session", "1"); }, token);
  await page.reload({ waitUntil: "domcontentloaded", timeout: 60_000 });
  await page.waitForSelector("text=Choose Photo", { timeout: 15_000 });

  // Wait for React hydration by polling for React internals
  await page.waitForFunction(() => {
    const input = document.querySelector('input[accept*="image"]');
    if (!input) return false;
    // Check for React's internal marker
    const keys = Object.keys(input);
    return keys.some(k => k.startsWith("__reactProps") || k.startsWith("__reactFiber"));
  }, { timeout: 20_000 }).catch(() => console.log("Timeout waiting for React hydration"));

  // Now check React state
  const state = await page.evaluate(() => {
    const input = document.querySelector('input[accept*="image"]') as HTMLInputElement;
    if (!input) return { error: "no input" };
    const keys = Object.keys(input).filter(k => k.startsWith("__react"));
    const rootEl = document.querySelector("#__next") || document.body;
    const rootKeys = Object.keys(rootEl).filter(k => k.startsWith("__react"));
    return { inputReactKeys: keys, rootReactKeys: rootKeys };
  });
  console.log("React state:", JSON.stringify(state, null, 2));
  
  // Now try upload
  const fs = require("fs");
  const path = require("path");
  const filePath = path.resolve(__dirname, "../../../image/image_04.jpg");
  const buf = fs.readFileSync(filePath);
  const b64 = buf.toString("base64");

  await page.evaluate(async ({ b64 }) => {
    const input = document.querySelector('input[accept*="image"]') as HTMLInputElement;
    if (!input) { console.error("No input"); return; }
    const resp = await fetch(`data:image/jpeg;base64,${b64}`);
    const blob = await resp.blob();
    const file = new File([blob], "image_04.jpg", { type: "image/jpeg" });
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }, { b64 });

  await page.waitForTimeout(5000);
  const canvas = page.locator("canvas").first();
  console.log("Canvas after hydration wait:", await canvas.isVisible().catch(() => "error"));
});
