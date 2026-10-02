/**
 * Test fixtures — the single point where every ZOZI E2E test begins.
 *
 * Extends Playwright's `test` and injects per-test:
 *   - `monitor`  — the per-test TestMonitor (anti-green-signal guard);
 *                  auto-finalized in the `after` hook, so every test reports
 *                  whether it actually performed meaningful work.
 *   - `commands` — Commands instance (browser actions + API calls, all
 *                  recorded for the anti-green-signal guard).
 *   - `workflows` — Workflows instance (composed feature flows, all recorded).
 *   - `expect`   — a tracked wrapper around Playwright's expect. Every matcher
 *                  invocation is recorded as an assertion; a test that never
 *                  asserts is rejected at the end of the test.
 *   - `verify`   — a verifier module with explicit matchers for use with
 *                  arbitrary values (`verify.equal(a, b)`, `verify.exists(x)`...).
 *
 * Usage:
 *   import { test, expect, commands, workflows, verify } from "../fixtures";
 *
 *   test("admin logs in", async ({ page, commands, workflows }) => {
 *     await commands.navigate(page, "/admin/login");
 *     await commands.fill(page, "Username", "admin@zozi.com");
 *     await commands.fill(page, "Password", "E2eAdmin#2026");
 *     await commands.click(page, "Sign in");
 *     await expect(page).toHaveURL(/\/admin\/dashboard/);
 *     workflows.assertAuthenticated(page);
 *   });
 *
 * Monitor finalization (per-test `after` hook):
 *   - A passed/flaky test must have performed at least one user action or API
 *     call plus at least one assertion. A green-signal test FAILS.
 *   - A test that already failed is finalized only to log the recorded-work
 *     summary, so the original failure is never masked.
 */

import { test as base, expect as baseExpect, type Page } from "@playwright/test";
import { TestMonitor } from "../src/monitor";
import { Commands } from "../src/actions";
import { Workflows } from "../src/workflows";

// ── Trackable expect wrapper ────────────────────────────────────────────────
//
// Playwright's `expect` returns a matcher-context object whose matcher methods
// capture `received` via closure at construction time. This wrapper proxies
// that context: every matcher call is recorded against the current test's
// monitor before delegating to the real matcher, so the matcher's original
// error surface is preserved.

function buildTrackedExpect(monitor: TestMonitor): typeof baseExpect {
  return new Proxy(baseExpect, {
    apply(target, thisArg, args) {
      // `args[0]` is the asserted value. Wrap the returned matcher context
      // so every matcher invocation is recorded.
      const context = Reflect.apply(target, thisArg, args);
      return new Proxy(context, {
        get(target, key, receiver) {
          const value = Reflect.get(target, key, receiver);
          if (typeof value === "function") {
            return new Proxy(value, {
              apply(innerTarget, innerThisArg, innerArgs) {
                let label = "assert";
                const matcher = (typeof key === "string" ? key : String(key)).replace(/^Symbol\(.+\)$/, "Symbol");
                if (innerArgs.length > 0) {
                  const first = innerArgs[0];
                  if (typeof first === "string") {
                    label = `.${matcher}("${first.slice(0, 80)}")`;
                  } else if (first instanceof RegExp) {
                    label = `.${matcher}(${first.source.slice(0, 80)})`;
                  } else if (first !== null && typeof first === "object") {
                    try {
                      label = `.${matcher}(${JSON.stringify(first).slice(0, 80)})`;
                    } catch {
                      label = `.${matcher}(object)`;
                    }
                  } else {
                    label = `.${matcher}(${String(first)})`;
                  }
                }
                monitor.trackAssert(label);
                return Reflect.apply(innerTarget, innerThisArg, innerArgs);
              },
            });
          }
          return value;
        },
      });
    },
  });
}

// ── Verifier helper for arbitrary values ────────────────────────────────────

export interface Verifier {
  /** `verify.equal(a, b)` — deep comparison via toEqual. */
  equal(a: unknown, b: unknown, message?: string): void;
  /** `verify.deepEqual(a, b)` — same as equal (renamed alias). */
  deepEqual(a: unknown, b: unknown, message?: string): void;
  /** `verify.isTrue(x)` — must be truthy. */
  isTrue(value: unknown, message?: string): void;
  /** `verify.isFalse(x)` — must be falsy. */
  isFalse(value: unknown, message?: string): void;
  /** `verify.isNull(x)` — must be null. */
  isNull(value: unknown, message?: string): void;
  /** `verify.isUndefined(x)` — must be undefined. */
  isUndefined(value: unknown, message?: string): void;
  /** `verify.exists(x)` — type-asserted existence (truthy). */
  exists<T>(value: T | null | undefined, message?: string): asserts value is T;
  /** `verify.notNull(x)` — type-asserted non-null. */
  notNull<T>(value: T | null | undefined, message?: string): asserts value is NonNullable<T>;
  /** `verify.contains(haystack, needle)` — array or string containment. */
  contains<T>(haystack: string | Array<unknown>, needle: unknown, message?: string): void;
}

// ── Fixture extension ────────────────────────────────────────────────────────

export interface ZOZIFixture {
  monitor: TestMonitor;
  commands: Commands;
  workflows: Workflows;
  expect: typeof baseExpect;
  verify: Verifier;
}

export const test = base.extend<ZOZIFixture>({
  // Page (default Playwright page) — injected so specs can reference it via
  // the fixture while all actions go through `commands`/`workflows`.
  page: async ({ page }, use) => {
    await use(page);
  },

  // Per-test monitor: constructed before the test body, finalized after it.
  // `auto: true` puts this in the after-hook chain, so finalization runs after
  // the test body AND after any per-test `afterEach` hook registered by a
  // dependency fixture. Finalization distinguishes passed vs failed tests so a
  // green-signal error never masks an actual assertion failure.
  monitor: [
    async ({}, use, testInfo) => {
      const title =
        testInfo.titlePath.length > 1
          ? testInfo.titlePath.slice(1).join(" ")
          : testInfo.title.slice(0, 160);

      const monitor = new TestMonitor(title);
      await use(monitor);

      if (testInfo.status === "passed" || testInfo.status === "flaky") {
        try {
          await monitor.finalize();
        } catch (err) {
          // A green-signal verdict on an otherwise-passing test is a real
          // failure of the test itself — surface it to the report.
          testInfo.fail(err as Error);
        }
      } else {
        // Test already failed: do not add a competing error. Just log the
        // recorded-work summary so the report shows what the test did.
        try {
          console.error(
            `[monitor] "${monitor.getTitle()}" — test failed; ` +
              `recorded ${monitor.getActions().length} actions: ${monitor.report()}`
          );
        } catch (e) {
          console.error(`[monitor] summary failed for "${monitor.getTitle()}": ${String(e)}`);
        }
      }
    },
    { auto: true, title: "per-test monitor (anti-green-signal)" },
  ],

  commands: async ({ monitor }, use) => {
    await use(new Commands(monitor));
  },

  workflows: async ({ monitor }, use) => {
    await use(new Workflows(monitor));
  },

  // Tracked expect — every matcher call counts as an assertion for the
  // anti-green-signal guard.
  expect: [
    async ({ monitor }, use, testInfo) => {
      const tracked = buildTrackedExpect(monitor);
      await use(tracked);
    },
    { auto: true, title: "tracked expect wrapper" },
  ],

  // Explicit verifier for value assertions.
  verify: async ({ expect: trackedExpect, monitor }, use) => {
    const verifier: Verifier = {
      equal(a: unknown, b: unknown, message?: string): void {
        trackedExpect(a).toEqual(b, message);
        monitor.trackAssert(message || `verify.equal: ${String(a)} === ${String(b)}`);
      },
      deepEqual(a: unknown, b: unknown, message?: string): void {
        verifier.equal(a, b, message);
      },
      isTrue(value: unknown, message?: string): void {
        trackedExpect(value).toBeTruthy(message);
        monitor.trackAssert(message || "verify.isTrue");
      },
      isFalse(value: unknown, message?: string): void {
        trackedExpect(value).toBeFalsy(message);
        monitor.trackAssert(message || "verify.isFalse");
      },
      isNull(value: unknown, message?: string): void {
        trackedExpect(value).toBeNull();
        monitor.trackAssert(message || "verify.isNull");
      },
      isUndefined(value: unknown, message?: string): void {
        trackedExpect(value).toBeUndefined();
        monitor.trackAssert(message || "verify.isUndefined");
      },
      exists<T>(value: T | null | undefined, message?: string): asserts value is T {
        trackedExpect(value).toBeTruthy(message || "verify.exists");
        monitor.trackAssert(message || "verify.exists");
      },
      notNull<T>(value: T | null | undefined, message?: string): asserts value is NonNullable<T> {
        trackedExpect(value).not.toBeNull(message || "verify.notNull");
        trackedExpect(value).not.toBeUndefined(message || "verify.notNull");
        monitor.trackAssert(message || "verify.notNull");
      },
      contains<T>(haystack: string | Array<unknown>, needle: unknown, message?: string): void {
        if (typeof haystack === "string") {
          trackedExpect(haystack).toContain(needle as string, message);
        } else {
          const locatorLike = haystack as Array<unknown>;
          if (Array.isArray(locatorLike)) {
            trackedExpect(locatorLike).toContainEqual(needle, message);
          } else {
            trackedExpect(haystack as any).toContain(needle, message);
          }
        }
        monitor.trackAssert(message || "verify.contains");
      },
    };
    await use(verifier);
  },
});

export type { Page, Locator, APIRequestContext, BrowserContext, Browser, TestInfo } from "@playwright/test";

// ── Re-exports from Playwright ──────────────────────────────────────────────

export {
  expect,
  describe,
  it,
  beforeAll,
  afterAll,
  beforeEach,
  afterEach,
  skip,
  only,
  slow,
  xtest,
  fixme,
} from "@playwright/test";
