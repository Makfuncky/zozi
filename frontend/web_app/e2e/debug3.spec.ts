import { expect, test, type Page } from "@playwright/test";
import path from "path";

const IMAGE_DIR = path.resolve(__dirname, "../../../image");

async function loginSupplier(page: Page) {
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
}

async function uploadImage(page: Page, fileName: string) {
  const filePath = path.join(IMAGE_DIR, fileName);
  const [fileChooser] = await Promise.all([
    page.waitForEvent("filechooser", { timeout: 15_000 }).catch(() => null),
    page.locator("label").filter({ hasText: "Choose Photo" }).click(),
  ]);
  if (fileChooser) {
    await fileChooser.setFiles(filePath);
    console.log("setFiles via chooser");
  } else {
    const input = page.locator('input[type="file"]').first();
    await input.setInputFiles(filePath);
    await input.evaluate((el) => {
      (el as HTMLInputElement).dispatchEvent(new Event("change", { bubbles: true }));
    });
    console.log("fallback used");
  }
  await page.waitForTimeout(3000);
}

test("debug3 with beforeEach", async ({ page }) => {
  await loginSupplier(page);
  await uploadImage(page, "image_04.jpg");
  const canvas = page.locator("canvas").first();
  console.log("Canvas visible:", await canvas.isVisible().catch(() => "error"));
});
