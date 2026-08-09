const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch();
  const base = "http://127.0.0.1:3000";

  async function runChat(locale) {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    page.on("console", (m) => { if (m.type() === "error") errors.push("console:" + m.text()); });

    // Set persisted locale before app hydrates
    await page.addInitScript((loc) => {
      window.localStorage.setItem("zozi_locale", JSON.stringify({ state: { locale: loc } }));
    }, locale);

    await page.goto(base + "/", { waitUntil: "networkidle" });

    // Open chatbot
    const chatBtn = page.getByRole("button", { name: /Chat/i });
    await chatBtn.first().click();

    const panel = page.locator("div.fixed.bottom-20").last();
    const input = panel.locator('input[placeholder]').first();
    await input.fill("show me black fashion under 300");
    await panel.locator('button[type="submit"]').click();

    // Assert the user message echoed into the panel
    await panel.getByText("show me black fashion under 300", { exact: true }).waitFor({ timeout: 10000 });

    // Wait for the bot reply (a bubble with product links OR arabic/english reply text)
    await page.waitForFunction(() => {
      const el = document.querySelector("div.fixed.bottom-20");
      if (!el) return false;
      const t = el.innerText || "";
      return /سحبت|pulled|I couldn't|لم أتمكن|Our return|مرحبًا/.test(t) && t.length > 200;
    }, { timeout: 15000 });

    const panelText = await panel.innerText();
    const hasArabic = /[\u0600-\u06FF]/.test(panelText);
    const hasProductLink = await panel.locator('a[href^="/products/"]').count();
    const promptBtns = await panel.locator("button").filter({ hasText: /اعرض|Show|أظهر|عرض/ }).count();

    const snippet = panelText.replace(/\s+/g, " ").slice(0, 400);
    console.log(`[${locale}] panelArabic=${hasArabic} panelProductLinks=${hasProductLink} panelPromptBtns=${promptBtns} errors=${errors.length}`);
    console.log("  snippet:", snippet);
    if (errors.length) console.log("  errors:", errors.slice(0, 5));
    await ctx.close();
  }

  await runChat("ar");
  await runChat("en");

  await browser.close();
})();
