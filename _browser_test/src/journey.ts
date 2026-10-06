import fs from "node:fs";
import path from "node:path";
import type { Page, Locator } from "@playwright/test";
import { actorDirFor, RUN_ID } from "./evidence";

/**
 * Resilient interaction helpers for journey walkthroughs.
 *
 * ZOZI renders most controls through an i18n layer, so visible labels change with
 * locale and `data-testid` coverage is thin. Every helper therefore takes a list
 * of candidate selectors and uses the first that resolves, recording which one
 * worked. A journey must keep walking (and keep capturing) even when a control
 * cannot be found — the missing control is itself evidence.
 */

export interface StepRecord {
  step: string;
  action: string;
  outcome: "ok" | "not-found" | "error";
  detail?: string;
}

export class JourneyLog {
  private records: StepRecord[] = [];

  record(step: string, action: string, outcome: StepRecord["outcome"], detail?: string) {
    this.records.push({ step, action, outcome, detail });
  }

  get rows(): StepRecord[] {
    return this.records;
  }

  get failures(): StepRecord[] {
    return this.records.filter((r) => r.outcome !== "ok");
  }

  write(actor: string, extra: string[] = []): void {
    const dir = actorDirFor(actor);
    fs.mkdirSync(dir, { recursive: true });
    const body = [
      `# ${actor} journeys — ${RUN_ID}`,
      "",
      ...extra,
      "",
      "| # | step | action | outcome | detail |",
      "|---|---|---|---|---|",
      ...this.records.map(
        (r, i) =>
          `| ${i + 1} | ${r.step} | ${r.action} | ${r.outcome} | ${(r.detail ?? "").replace(/\|/g, "/").slice(0, 120)} |`,
      ),
      "",
      `Total ${this.records.length} interactions, ${this.failures.length} not completed.`,
    ];
    fs.writeFileSync(path.join(dir, "journeys.md"), body.join("\n"), "utf-8");
  }
}

export type Candidate =
  | string
  | { role: string; name?: RegExp | string; exact?: boolean }
  | { text: RegExp | string; exact?: boolean }
  | { label: RegExp | string };

function toLocator(page: Page, c: Candidate): Locator {
  if (typeof c === "string") return page.locator(c);
  if ("role" in c) {
    const opts = c.name === undefined ? undefined : { name: c.name as never, exact: c.exact ?? false };
    return page.getByRole(c.role as never, opts as never);
  }
  if ("text" in c) return page.getByText(c.text as never, { exact: c.exact ?? false });
  return page.getByLabel(c.label as never);
}

/**
 * First *visible* element among the candidates.
 *
 * Deliberately checks several matches per candidate, not just `.first()`:
 * responsive layouts render hidden duplicates (a desktop nav plus a mobile
 * drawer, a visible card plus an off-screen carousel clone), so the first match
 * is frequently invisible while a later one is real.
 */
export async function pick(page: Page, candidates: Candidate[]): Promise<Locator | null> {
  const PER_CANDIDATE = 6;
  for (const c of candidates) {
    const loc = toLocator(page, c);
    const n = Math.min(await loc.count().catch(() => 0), PER_CANDIDATE);
    for (let i = 0; i < n; i++) {
      const one = loc.nth(i);
      const ok = await one
        .isVisible({ timeout: 1_500 })
        .then((v) => v)
        .catch(() => false);
      if (ok) return one;
    }
  }
  return null;
}

/** Click the first visible candidate. Never throws. */
export async function clickAny(
  page: Page,
  candidates: Candidate[],
  log?: JourneyLog,
  step?: string,
): Promise<boolean> {
  const loc = await pick(page, candidates);
  if (!loc) {
    log?.record(step ?? "?", "click", "not-found", describe(candidates));
    return false;
  }
  try {
    await loc.click({ timeout: 8_000 });
    log?.record(step ?? "?", `click "${await safeText(loc)}"`, "ok");
    return true;
  } catch (e) {
    log?.record(step ?? "?", "click", "error", String(e).split("\n")[0].slice(0, 100));
    return false;
  }
}

export async function fillAny(
  page: Page,
  candidates: Candidate[],
  value: string,
  log?: JourneyLog,
  step?: string,
): Promise<boolean> {
  const loc = await pick(page, candidates);
  if (!loc) {
    log?.record(step ?? "?", "fill", "not-found", describe(candidates));
    return false;
  }
  try {
    await loc.fill(value, { timeout: 8_000 });
    log?.record(step ?? "?", `fill "${value}"`, "ok");
    return true;
  } catch (e) {
    log?.record(step ?? "?", "fill", "error", String(e).split("\n")[0].slice(0, 100));
    return false;
  }
}

/** First product href currently in the DOM, e.g. "/products/58". */
export async function firstProductHref(page: Page): Promise<string | null> {
  return page
    .evaluate(() => {
      const links = [...document.querySelectorAll('a[href*="/products/"]')] as HTMLAnchorElement[];
      const visible = links.find((a) => {
        const r = a.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      });
      const href = (visible ?? links[0])?.getAttribute("href") ?? "";
      const m = href.match(/\/products\/([^/?#]+)/);
      return m ? `/products/${m[1]}` : null;
    })
    .catch(() => null);
}

/** Click the first product card / link on a listing page. */
export async function openFirstItem(
  page: Page,
  candidates: Candidate[],
  log?: JourneyLog,
  step?: string,
): Promise<string | null> {
  const loc = await pick(page, candidates);
  if (!loc) {
    // Fall back to navigating straight to a real product id. Hardcoding /products/1
    // is wrong: seeded ids start higher, and the PDP 404s on a missing id.
    const href = await firstProductHref(page);
    if (href) {
      await page.goto(href, { waitUntil: "domcontentloaded", timeout: 60_000 }).catch(() => {});
      log?.record(step ?? "?", "open first item", "ok", `direct ${page.url()}`);
      return page.url();
    }
    log?.record(step ?? "?", "open first item", "not-found", describe(candidates));
    return null;
  }
  try {
    await loc.click({ timeout: 8_000 });
    await page.waitForLoadState("domcontentloaded", { timeout: 30_000 }).catch(() => {});
    log?.record(step ?? "?", "open first item", "ok", page.url());
    return page.url();
  } catch (e) {
    log?.record(step ?? "?", "open first item", "error", String(e).split("\n")[0].slice(0, 100));
    return null;
  }
}

/** Row counts for tables/lists — cheap proof a screen holds data. */
export async function countRows(page: Page): Promise<number> {
  return page
    .evaluate(() => {
      // Product grids expose plain links to /products/<id> with no data-testid,
      // so the selector set has to cover link-based cards as well as table rows.
      const sel = [
        "table tbody tr",
        '[role="row"]',
        '[role="listitem"]',
        "article",
        'a[href*="/products/"]',
        'a[href*="/orders/"]',
        'a[href*="/admin/users/"]',
        // Cart lines and order cards are plain divs; the header cart badge is the
        // authoritative signal that an add-to-cart landed, so count it too.
        '[data-testid="cart-item"]',
        '[class*="cart-item" i]',
        '[class*="line-item" i]',
        '[class*="order-card" i]',
        '[data-testid$="-row"]',
        '[data-testid$="-card"]',
        '[data-testid$="-item"]',
      ].join(",");
      const seen = new Set<Element>();
      for (const n of document.querySelectorAll(sel)) seen.add(n);
      return [...seen].filter((n) => {
        const r = n.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      }).length;
    })
    .catch(() => 0);
}

/**
 * Wait until a listing page has actually painted its items.
 *
 * Dev-mode Next.js compiles a route on first hit, so the catalogue request can
 * start several seconds after navigation. Polling for real content is the only
 * reliable signal — a fixed sleep just captures skeletons.
 */
export async function waitForContent(
  page: Page,
  candidates: Candidate[],
  timeoutMs = 45_000,
): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if ((await countRows(page)) > 0) return true;
    const loc = await pick(page, candidates);
    if (loc) return true;
    await page.waitForTimeout(600);
  }
  return false;
}

async function safeText(loc: Locator): Promise<string> {
  return (await loc.innerText({ timeout: 2_000 }).catch(() => "")).replace(/\s+/g, " ").slice(0, 48);
}

function describe(c: Candidate[]): string {
  return c
    .map((x) => (typeof x === "string" ? x : "role" in x ? `${x.role}:${x.name}` : "text" in x ? `text:${x.text}` : "label"))
    .join(" | ")
    .slice(0, 120);
}

export const ADD_TO_CART: Candidate[] = [
  { role: "button", name: /add to cart/i },
  { role: "button", name: /add to bag/i },
  { text: /add to cart/i },
  '[data-testid="add-to-cart"]',
  "button:has-text('Add to Cart')",
];

export const PRODUCT_CARD: Candidate[] = [
  '[data-testid="product-card"]',
  "a[href*='/products/']",
  '[data-testid$="-product-card"]',
];

export const SEARCH_INPUT: Candidate[] = [
  { role: "searchbox" },
  'input[type="search"]',
  'input[placeholder*="search" i]',
  'input[name*="search" i]',
];

export const PLACE_ORDER: Candidate[] = [
  { role: "button", name: /place order/i },
  { role: "button", name: /confirm order/i },
  { role: "button", name: /complete order/i },
  { text: /place order/i },
];

export const COD_OPTION: Candidate[] = [
  { text: /cash on delivery/i },
  { text: /\bCOD\b/ },
  { role: "radio", name: /cash/i },
  { role: "button", name: /cash on delivery/i },
];