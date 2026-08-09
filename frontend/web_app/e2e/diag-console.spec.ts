import { test, type ConsoleMessage } from "@playwright/test";

test("console capture on home", async ({ page }) => {
  const msgs: { t: string; type: string; text: string }[] = [];
  page.on("console", (m: ConsoleMessage) => {
    msgs.push({ t: new Date().toISOString().slice(11, 23), type: m.type(), text: m.text().slice(0, 160) });
  });
  page.on("pageerror", (e) => msgs.push({ t: "ERR", type: "pageerror", text: e.message.slice(0, 200) }));

  const t0 = Date.now();
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 60_000 });
  // measure time to hydration: when document.body has a child with data-app-frame
  let tInteractive = -1;
  while (Date.now() - t0 < 40_000) {
    const ready = await page.evaluate(() => {
      const f = document.querySelector("[data-app-frame]");
      return !!f && f.childElementCount > 0;
    }).catch(() => false);
    if (ready && tInteractive < 0) { tInteractive = Date.now() - t0; break; }
    await page.waitForTimeout(500);
  }
  await page.waitForTimeout(2000);
  console.log("timeToInteractive(approx ms):", tInteractive);
  console.log("MSG COUNT:", msgs.length);
  console.log(JSON.stringify(msgs.slice(0, 40), null, 2));
});
