import { expect, test, type Page } from "@playwright/test";
import path from "path";

const IMAGE_DIR = path.resolve(__dirname, "../../../image");

test("debug5 - check React internal state", async ({ page }) => {
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

  // Check React event system on the input
  const inputInfo = await page.evaluate(() => {
    const input = document.querySelector('input[accept*="image"]') as HTMLInputElement;
    if (!input) return { error: "No input found" };
    // Find React props on input
    const reactKey = Object.keys(input).find(k => k.startsWith("__reactProps"));
    const reactFiberKey = Object.keys(input).find(k => k.startsWith("__reactFiber"));
    // Check all listeners on the root
    const root = document.getElementById("__next") || document.getElementById("root") || document.body;
    const rootReactKeys = Object.keys(root).filter(k => k.startsWith("__react"));
    // Check the onChange
    const hasNativeChange = typeof input.onchange === "function";
    // Listen for coming change
    return {
      reactPropsOnInput: !!reactKey,
      reactFiberOnInput: !!reactFiberKey,
      rootReactKeys: rootReactKeys.slice(0, 5),
      hasNativeChange,
    };
  });
  console.log("Input info:", JSON.stringify(inputInfo, null, 2));
});
