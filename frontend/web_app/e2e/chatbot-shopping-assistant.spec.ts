import { expect, test, type Page } from "@playwright/test";

test.describe.configure({ timeout: 120_000 });

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function chatPanel(page: Page) {
  return page.locator("div.fixed.bottom-20.right-4.z-50").first();
}

async function openChat(page: Page) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2000);
  const panel = chatPanel(page);
  if (!(await panel.isVisible())) {
    const toggle = page.locator("button.fixed.bottom-4.right-4.z-50").first();
    await expect(toggle).toBeVisible({ timeout: 15_000 });
    for (let attempt = 0; attempt < 2; attempt += 1) {
      await toggle.click({ force: true });
      if (await panel.isVisible()) {
        break;
      }
      await page.waitForTimeout(300);
    }
    if (!(await panel.isVisible())) {
      await page.goto("/chatbot", { waitUntil: "domcontentloaded" });
    }
  }
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(panel.locator("button[type='submit']", { hasText: /^go$/i }).first()).toBeVisible({ timeout: 15_000 });
}

async function sendPrompt(page: Page, prompt: string) {
  const chatForm = chatPanel(page).locator("form").first();
  const input = chatForm.locator("input").first();
  await input.fill(prompt);
  const submitButton = chatForm.locator("button[type='submit']").first();
  await submitButton.click();
  await expect(page.getByText(prompt, { exact: true })).toBeVisible({ timeout: 15_000 });
}

async function clickFollowUpPrompt(page: Page, matcher: RegExp = /^show /i) {
  const promptButton = chatPanel(page).getByRole("button", { name: matcher }).first();
  await expect(promptButton).toBeVisible({ timeout: 20_000 });
  const promptText = ((await promptButton.textContent()) || "").trim();
  const chatbotResponse = page.waitForResponse(
    (response) => response.url().includes("/chatbot") && response.request().method() === "POST" && response.status() < 400,
    { timeout: 30_000 },
  );
  await promptButton.click();
  await chatbotResponse;
  if (promptText) {
    await expect(page.getByText(new RegExp(`^${escapeRegex(promptText)}$`, "i")).last()).toBeVisible({ timeout: 20_000 });
  }
}

test("chatbot offers close-match fashion recommendations for realistic prompts", async ({ page }) => {
  test.slow();
  await openChat(page);

  await sendPrompt(page, "show me black bra");

  await expect(page.getByText(/don't have an exact black bra/i)).toBeVisible({ timeout: 20_000 });
  await expect(chatPanel(page).locator("a[href^='/products/']").first()).toBeVisible({ timeout: 20_000 });
  await clickFollowUpPrompt(page, /^show /i);
  await expect(chatPanel(page).locator("a[href^='/products/']").nth(1)).toBeVisible({ timeout: 20_000 });
});

test("chatbot keeps budget-aware apparel suggestions in the live widget", async ({ page }) => {
  test.slow();
  await openChat(page);

  await sendPrompt(page, "need a hoodie under 200");

  await expect(page.getByText(/don't have an exact hoodie/i)).toBeVisible({ timeout: 20_000 });
  await expect(chatPanel(page).locator("a[href^='/products/']").first()).toBeVisible({ timeout: 20_000 });
  await expect(chatPanel(page).getByRole("button", { name: /show cheaper alternatives|show options under|show top-rated options/i }).first()).toBeVisible({ timeout: 20_000 });
});