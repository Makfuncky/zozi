const { chromium } = require("playwright");
const BASE = "http://localhost:3000";
const OUT = "C:\\Users\\user\\AppData\\Local\\Temp\\kilo";
const REFRESH = process.env.CUSTOMER_REFRESH || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMCIsImV4cCI6MTc4NDc1NzA2NCwidHlwZSI6InJlZnJlc2giLCJqdGkiOiJhZjU0MjVlZWIyYjg0ZGM5OTViZGM4NWFmNWQyNGZjOSIsImZhbWlseV9pZCI6ImJlZWMyYWNlNWZlYzRlYTc4ZjYzNTk3OTYzNmViMzRiIn0.-gbJ0AdyE9br1mPd-u5XCWrh6eNMqB6iE-L5K09lDqw";

(async () => {
  const browser = await chromium.launch();
  try {
    const ctx = await browser.newContext();
    await ctx.addCookies([{ name: "refresh_token", value: REFRESH, domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax" }]);

    // Patch fetch BEFORE app boot so:
    //  1) the cart store's syncOnLogin() cannot wipe our injected local cart
    //     with the (empty) server cart — we mirror the localStorage cart back.
    //  2) we capture the access token from /auth/refresh so verification
    //     fetches can attach it; and we auto-attach it to __api/auth calls.
    await ctx.addInitScript(() => {
      const KEY = "cart-storage";
      window.__accessToken = null;
      const origFetch = window.fetch.bind(window);
      const mirrorCart = (u) => {
        if (typeof u === "string" && (u.includes("/cart/sync") || u.endsWith("/cart"))) {
          let items = [];
          try { items = JSON.parse(localStorage.getItem(KEY) || "[]"); } catch {}
          return new Response(JSON.stringify({ items }), {
            status: 200,
            headers: { "content-type": "application/json" },
          });
        }
        return null;
      };
      window.fetch = (u, init) => {
        const stub = mirrorCart(u);
        if (stub) return Promise.resolve(stub);
        const url = typeof u === "string" ? u : u.url;
        init = init || {};
        const headers = new Headers(init.headers || {});
        if ((url.includes("/__api/") || url.includes("/auth/")) && window.__accessToken && !headers.has("Authorization")) {
          headers.set("Authorization", "Bearer " + window.__accessToken);
        }
        const patchedInit = { ...init, headers };
        return origFetch(u, patchedInit).then(async (res) => {
          try {
            if (url.includes("/auth/refresh") || url.includes("/auth/login") || url.includes("/auth/me")) {
              const ct = res.headers.get("content-type") || "";
              if (ct.includes("application/json")) {
                const clone = res.clone();
                const j = await clone.json().catch(() => null);
                if (j && j.access_token) window.__accessToken = j.access_token;
              }
            }
          } catch {}
          return res;
        });
      };
    });

    const page = await ctx.newPage();
    page.on("response", (r) => { const u = r.url(); if (u.includes("/__api/") || u.includes("/auth/")) console.log("NET", r.status(), u.replace(BASE, "")); });
    await page.goto(BASE + "/", { waitUntil: "domcontentloaded" });
    await page.evaluate(() => {
      localStorage.setItem("zozi_has_session", "1");
      // Inject a cart item so checkout renders the payment-method section.
      localStorage.setItem(
        "cart-storage",
        JSON.stringify([
          { id: 1, name: "Test Product", price: 100, image_url: null, description: "", category: "", stock: 10, is_active: true, quantity: 1, line_id: "1::::", selected_size: "", selected_color: "" },
        ])
      );
    });
    console.log("[setup] cookie + has_session + cart injected");
    await page.goto(BASE + "/checkout", { waitUntil: "domcontentloaded" });
    try {
      await page.waitForFunction(() => /paymob/i.test(document.body.innerText), { timeout: 30000 });
    } catch (e) {
      const body = await page.textContent("body");
      console.log("BODY:", body.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").slice(0, 400));
      const rb = await page.evaluate(async () => {
        let rf = "n/a";
        try { const r = await fetch("/auth/refresh", { method: "POST", credentials: "include" }); rf = r.status + " " + (await r.text()).slice(0, 120); } catch (e2) { rf = "ERR " + e2.message; }
        let pm = "n/a";
        try { const r2 = await fetch("/__api/payments/methods", { credentials: "include", headers: { Authorization: "Bearer " + (window.localStorage.getItem("x") || "") } }); pm = r2.status + " " + (await r2.text()).slice(0, 120); } catch (e3) { pm = "ERR " + e3.message; }
        return { rf, pm, hasSession: localStorage.getItem("zozi_has_session") };
      });
      console.log("REFRESH:", rb.rf, "| METHODS:", rb.pm, "| has_session:", rb.hasSession);
      throw e;
    }
    const body = await page.textContent("body");
    const ok = /paymob/i.test(body);
    console.log("checkout shows Paymob option:", ok);
    await page.screenshot({ path: OUT + "\\e2e_checkout_paymob.png", fullPage: true });
    // Also confirm via the exact endpoint checkout consumes.
    const api = await page.evaluate(async () => {
      const token = window.__accessToken;
      const r = await fetch("/__api/payments/methods", {
        credentials: "include",
        headers: token ? { Authorization: "Bearer " + token } : undefined,
      });
      if (!r.ok) return { ok: false, status: r.status };
      const j = await r.json();
      return { ok: true, codes: (j.gateways || []).map((g) => g.provider_code) };
    });
    console.log("in-browser /payments/methods:", JSON.stringify(api));
    if (ok && api.ok && api.codes.includes("paymob")) {
      console.log("\n=== STOREFRONT E2E RESULT: PASS ===");
      console.log("  - Customer checkout renders the plug-and-play 'Paymob' gateway");
      console.log("  - Storefront /payments/methods returns it client-side");
      process.exitCode = 0;
    } else {
      throw new Error("storefront did not render custom gateway");
    }
  } catch (e) {
    console.error("\n=== STOREFRONT E2E RESULT: FAIL ===");
    console.error(e && e.stack ? e.stack : e);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
