import fs from "node:fs";
import path from "node:path";
import { test as base, expect, type Page } from "@playwright/test";

/**
 * Evidence capture.
 *
 * The regression layer asserts. This module records. Together they answer two
 * different questions:
 *   - regression spec  -> "did behaviour change?"
 *   - evidence step()  -> "what does this screen actually look like, for this
 *                          actor, on this run?"
 *
 * Every `step()` writes a before and an after screenshot, so a captured run shows
 * the screen state on both sides of an action even when nothing asserts on it.
 */

export const RUN_ID = process.env.RUN_ID || new Date().toISOString().replace(/[:.]/g, "-");
export const EVIDENCE_ROOT = path.resolve(
  process.env.EVIDENCE_DIR || path.join(process.cwd(), "evidence", RUN_ID),
);

/** Third-party services that cost money or send real messages. */
const EXTERNAL_HOSTS = [
  "stripe.com",
  "api.stripe.com",
  "checkout.stripe.com",
  "paypal.com",
  "api.paypal.com",
  "www.paypal.com",
  "tap.company",
  "paytabs.com",
  "thawani.om",
  "api.twilio.com",
  "twilio.com",
  "api.sendgrid.com",
  "api.mailgun.org",
  "resend.com",
  "api.sentry.io",
  "o1.ingest.sentry.io",
  "glitchtip.com",
  "app.glitchtip.com",
];

function slug(text: string): string {
  return (
    text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 48) || "step"
  );
}

function actorDir(actor: string): string {
  const dir = path.join(EVIDENCE_ROOT, actor);
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

/** Exposed so sibling modules can write into the same per-actor folder. */
export const actorDirFor = actorDir;

let counter = 0;
function nextPrefix(actor: string): string {
  counter += 1;
  return String(counter).padStart(3, "0");
}

/**
 * Wait for a page to actually finish loading.
 *
 * Screenshots taken straight after `goto` catch skeleton placeholders and empty
 * stat cards, which is useless as evidence. This waits for the network to go
 * quiet and for loading affordances to disappear, so the capture shows data.
 */
export async function settle(page: Page, opts: { quietMs?: number; budgetMs?: number } = {}) {
  const quietMs = opts.quietMs ?? 1_200;
  // Dev-mode Next.js compiles a route on first hit, so the first visit to a page
  // can take tens of seconds. Once warm, responses land in a second or two — a
  // large default here multiplied by 60 admin steps is what made that journey
  // time out. Callers that hit a cold route pass an explicit larger budget.
  const budgetMs = opts.budgetMs ?? 20_000;

  await page.waitForLoadState("domcontentloaded", { timeout: budgetMs }).catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: budgetMs }).catch(() => {});

  // Loading affordances ZOZI uses: skeleton blocks, spinners, progress bars and
  // the command-center INITIALISING banner.
  const LOADING = [
    '[class*="skeleton"]',
    '[class*="animate-pulse"]',
    '[data-loading="true"]',
    '[aria-busy="true"]',
    '[role="progressbar"]',
    'text=/initialising/i',
    'text=/loading\\.\\.\\./i',
  ].join(", ");

  const deadline = Date.now() + budgetMs;
  while (Date.now() < deadline) {
    const busy = await page
      .evaluate((sel) => {
        const nodes = [...document.querySelectorAll(sel)];
        return nodes.filter((n) => {
          const r = n.getBoundingClientRect();
          return r.width > 0 && r.height > 0;
        }).length;
      }, LOADING)
      .catch(() => 0);
    if (!busy) break;
    await page.waitForTimeout(400);
  }

  // One more network beat so late-arriving payloads paint.
  await page.waitForTimeout(quietMs);
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r(null)))).catch(() => {});
}

/**
 * Record one user-visible step: act, settle, then capture.
 *
 * `fn` may throw — the after-shot is still written, so a crash leaves the screen
 * state that caused it.
 */
export async function step(
  page: Page,
  actor: string,
  name: string,
  fn: () => Promise<unknown>,
  opts: { settle?: boolean } = {},
): Promise<void> {
  const dir = actorDir(actor);
  const prefix = `${nextPrefix(actor)}-${slug(name)}`;

  await page
    .screenshot({ path: path.join(dir, `${prefix}-before.png`), fullPage: true })
    .catch(() => {});

  // Diagnostic only. Deliberately NOT expect.soft(): a soft assertion still
  // fails the test at the end even when caught, and evidence collection must
  // never turn a rendering quirk into a red run.
  const bodyVisible = await page
    .locator("body")
    .isVisible()
    .catch(() => false);
  if (!bodyVisible) {
    fs.appendFileSync(
      path.join(actorDir(actor), "diagnostics.log"),
      `${new Date().toISOString()} ${actor} ${name}: body not visible at "${page.url()}"\n`,
    );
  }

  try {
    await fn();
    if (opts.settle !== false) await settle(page);
  } finally {
    await page
      .screenshot({ path: path.join(dir, `${prefix}-after.png`), fullPage: true })
      .catch(() => {});
  }
}

/** Record a step that is expected to be denied, capturing the state that proves it. */
export async function deniedStep(
  page: Page,
  actor: string,
  name: string,
  fn: () => Promise<void>,
): Promise<void> {
  await step(page, actor, name, async () => {
    await fn();
    const url = page.url();
    const body = (await page.locator("body").innerText().catch(() => "")) ?? "";
    fs.writeFileSync(
      path.join(actorDir(actor), `${slug(name)}-denial.txt`),
      [`url: ${url}`, "", body.slice(0, 4000)].join("\n"),
      "utf-8",
    );
  });
}

/**
 * Mock only the true externals. Everything else must hit the real backend —
 * mocking the app's own API turns a walkthrough into a fiction.
 */
export async function mockExternals(page: Page): Promise<string[]> {
  const installed: string[] = [];
  for (const host of EXTERNAL_HOSTS) {
    const pattern = `**://*.${host}/**`;
    await page.route(pattern, async (route) => {
      const url = route.request().url();
      // Never let a real payment or SMS request leave the machine.
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ mocked: true, host, url, note: "external intercepted by _browser_test" }),
      });
    });
    installed.push(pattern);
  }
  return installed;
}

/**
 * Report what the page is complaining about, so "what is the problem in the
 * browser" is answered by the artifact rather than by reading the console.
 */
export async function collectDiagnostics(page: Page): Promise<{
  url: string;
  title: string;
  consoleErrors: string[];
  failedRequests: string[];
  httpErrors: string[];
  overflowPx: number;
  emptyStates: number;
}> {
  const consoleErrors: string[] = [];
  const failedRequests: string[] = [];
  const httpErrors: string[] = [];

  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text().slice(0, 500));
  });
  page.on("requestfailed", (r) => {
    failedRequests.push(`${r.method()} ${r.url()} — ${r.failure()?.errorText ?? "failed"}`.slice(0, 500));
  });
  page.on("response", (r) => {
    if (r.status() >= 400) httpErrors.push(`${r.status()} ${r.request().method()} ${r.url()}`.slice(0, 500));
  });

  const overflowPx = await page
    .evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
    .catch(() => 0);

  const emptyStates = await page
    .evaluate(() => {
      const sel = "h1, [role=heading]";
      return [...document.querySelectorAll(sel)].filter((el) => {
        const r = el.getBoundingClientRect();
        return r.width === 0 || r.height === 0;
      }).length;
    })
    .catch(() => 0);

  return {
    url: page.url(),
    title: await page.title().catch(() => ""),
    consoleErrors,
    failedRequests,
    httpErrors,
    overflowPx,
    emptyStates,
  };
}

/** Write a per-actor markdown summary of what the run saw. */
export function writeActorReport(actor: string, lines: string[]): void {
  fs.mkdirSync(actorDir(actor), { recursive: true });
  fs.writeFileSync(
    path.join(actorDir(actor), "report.md"),
    [`# ${actor} — ${RUN_ID}`, "", ...lines, ""].join("\n"),
    "utf-8",
  );
}

export const test = base;
