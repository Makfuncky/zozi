import { expect, test } from "@playwright/test";
import path from "path";

const IMAGE_DIR = path.resolve(__dirname, "../../../image");

test("exact debug", async ({ page }) => {
  // EXACTLY what main test does
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

  // Now upload - try filechooser first, fallback to setInputFiles
  const filePath = path.join(IMAGE_DIR, "image_04.jpg");

  const fileChooser = await page.waitForEvent("filechooser", { timeout: 5000 }).catch(() => null);
  console.log("FileChooser auto-caught:", !!fileChooser);

  // Try filechooser via label click
  const fc2 = await Promise.race([
    page.waitForEvent("filechooser", { timeout: 8000 }).then(() => "filechooser_fired").catch(() => null),
    page.locator("label").filter({ hasText: "Choose Photo" }).click().then(() => "clicked").catch(() => null),
  ]);
  console.log("Label click result:", fc2);
  
  // After label click, check if filechooser appeared
  const fc3 = await page.waitForEvent("filechooser", { timeout: 2000 }).catch(() => null);
  console.log("FileChooser after click:", !!fc3);
  if (fc3) {
    await fc3.setFiles(filePath);
    console.log("Set files via filechooser");
  } else {
    // Fallback
    const input = page.locator('input[type="file"]').first();
    await input.setInputFiles(filePath);
    await input.evaluate((el) => {
      (el as HTMLInputElement).dispatchEvent(new Event("change", { bubbles: true }));
    });
    console.log("Set files via fallback");
  }
  
  await page.waitForTimeout(5000);
  const canvas = page.locator("canvas");
  console.log("Canvas visible:", await canvas.isVisible().catch(() => "error"));
  console.log("URL:", page.url());
});
