/**
 * Command Registry — the single source of browser actions for every test.
 *
 * Every test performs work by calling `commands.<action>(page, ...)`. Each
 * command:
 *   1. resolves the target locators (label-based or explicit),
 *   2. performs the Playwright action with sensible timeouts,
 *   3. records the action in the test monitor (anti-green-signal guard).
 *
 * Patterns:
 *   - `navigate(page, '/products')`           — named or explicit URL
 *   - `click(page, 'Sign in')`                — by label, then by any locator
 *   - `fill(page, 'Email', 'x@y.com')`        — by label/name, then input
 *   - `clickWithFallback(page, selector, opts)` — robust multi-strategy click
 *
 * Usage in a spec:
 *   import { test, expect } from '../fixtures';
 *   test('admin logs in', async ({ page, commands }) => {
 *     await commands.navigate(page, '/admin/login');
 *     await commands.fill(page, 'email', 'admin@zozi.com');
 *     await commands.fill(page, 'password', 'E2eAdmin#2026');
 *     await commands.click(page, 'Sign in');
 *     await expect(page).toHaveURL(/\/admin\/dashboard/);
 *   });
 */

import type { Page, Locator, FrameLocator } from '@playwright/test';
import { TestMonitor } from './monitor';

export interface CommandPage {
  page: Page;
  monitor: TestMonitor;
  context(): Page['context'];
}

export interface ClickOptions {
  waitBefore?: number;
  force?: boolean;
  noWaitAfter?: boolean;
}

export class Commands {
  private monitor: TestMonitor;

  constructor(monitor: TestMonitor) {
    this.monitor = monitor;
  }

  // ───────── Navigation ───────────────────────────────────────────────

  /** Navigate to a URL (absolute or relative to baseURL). */
  async navigate(page: Page, url: string, opts?: { waitUntil?: string; timeout?: number }): Promise<void> {
    this.monitor.trackNavigation(url);
    await page.goto(url, { waitUntil: opts?.waitUntil ?? 'domcontentloaded', timeout: opts?.timeout ?? 45_000 });
  }

  /** Navigate then wait for the URL to match a pattern. */
  async navigateTo(page: Page, url: string, pattern: RegExp, timeoutMs = 60_000): Promise<void> {
    await this.navigate(page, url);
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      if (pattern.test(page.url())) return;
      await page.waitForTimeout(250);
    }
    throw new Error(`Timed out waiting for URL to match ${pattern}; current URL: ${page.url()}`);
  }

  // ───────── Mouse / pointer ───────────────────────────────────────────

  /** Click a label, falling back to explicit locators. */
  async click(
    page: Page,
    target: string | Locator,
    opts?: ClickOptions,
    label?: string
  ): Promise<void> {
    const loc = await this.resolveLocator(page, target, 'button, a, [role="button"]', label ?? target);
    this.monitor.trackClick(label ?? target);
    await loc.click({ force: opts?.force ?? false, waitBefore: opts?.waitBefore, noWaitAfter: opts?.noWaitAfter });
  }

  /** Double-click. */
  async dblClick(page: Page, target: string | Locator, label?: string): Promise<void> {
    const loc = await this.resolveLocator(page, target, '*');
    this.monitor.trackClick(label ?? target);
    await loc.dblclick();
  }

  /** Hover. */
  async hover(page: Page, target: string | Locator, label?: string): Promise<void> {
    const loc = await this.resolveLocator(page, target, '*');
    this.monitor.trackClick(label ?? target);
    await loc.hover();
  }

  /** Right-click (for context menus / popups). */
  async rightClick(page: Page, target: string | Locator, label?: string): Promise<void> {
    const loc = await this.resolveLocator(page, target, '*');
    this.monitor.trackClick(label ?? target);
    await loc.click({ button: 'right' });
  }

  // ───────── Keyboard / fill ──────────────────────────────────────────

  /** Fill an input by label/name/type, with fallback chain. */
  async fill(
    page: Page,
    target: string | Locator,
    value: string,
    opts?: { clear?: boolean; timeout?: number }
  ): Promise<void> {
    const { locator, kind } = await this.resolveInput(page, target);
    this.monitor.trackFill(kind);
    if (opts?.clear) {
      await locator.clear({ timeout: opts?.timeout ?? 15_000 });
    }
    await locator.fill(value, { timeout: opts?.timeout ?? 15_000 });
    await locator.dispatchEvent('input');
    await locator.dispatchEvent('change');
    await locator.pressSequentially('', { timeout: 1000 });
  }

  /** Type into a contenteditable or any element. */
  async type(page: Page, target: string | Locator, value: string, label?: string): Promise<void> {
    const loc = await this.resolveLocator(page, target, '*');
    this.monitor.trackType(label ?? target);
    await loc.click({ position: { x: 2, y: 2 } });
    await loc.pressSequentially(value, { delay: 20 });
  }

  /** Select an option from a select element. */
  async selectOption(page: Page, target: string | Locator, value: string, label?: string): Promise<void> {
    const { locator, kind } = await this.resolveInput(page, target);
    this.monitor.trackSelect(kind);
    await locator.selectOption(value, { timeout: 15_000 });
  }

  /** Check/uncheck a checkbox. */
  async check(page: Page, target: string | Locator, label?: string, checked = true): Promise<void> {
    const { locator, kind } = await this.resolveInput(page, target);
    const isChecked = await locator.isChecked();
    if (isChecked !== checked) {
      this.monitor.trackClick(kind);
      await locator.click({ force: true });
      await locator.waitFor({ state: checked ? 'checked' : 'unchecked', timeout: 15_000 });
    }
  }

  // ───────── File upload ──────────────────────────────────────────────

  /** Upload a file to a file input. */
  async uploadFile(page: Page, target: string | Locator, filePath: string, label?: string): Promise<void> {
    const { locator, kind } = await this.resolveInput(page, target);
    this.monitor.trackUpload(kind);
    await locator.setInputFiles(filePath, { timeout: 30_000 });
  }

  // ───────── Focus / misc ──────────────────────────────────────────────

  /** Press a key while focused. */
  async press(page: Page, target: string | Locator, key: string, label?: string): Promise<void> {
    const loc = await this.resolveLocator(page, target, '*');
    this.monitor.trackClick(label ?? target);
    await loc.press(key, { timeout: 10_000 });
  }

  /** Wait for an element to be visible. */
  async waitForVisible(page: Page, target: string | Locator, label?: string, timeoutMs = 30_000): Promise<void> {
    const loc = await this.resolveLocator(page, target, '*');
    await loc.waitFor({ state: 'visible', timeout: timeoutMs });
    this.monitor.trackAssert(label ?? target);
  }

  // ───────── Network (API) ─────────────────────────────────────────────

  /** GET request via page.request. */
  async getApi<T = unknown>(page: Page, path: string, expectedStatus = 200): Promise<{ status: number; body: T }> {
    this.monitor.trackApiGet(path);
    const res = await page.request.get(`${process.env.API_BASE_URL || 'http://127.0.0.1:8000'}${path}`, {
      timeout: 30_000,
      failOnStatusCode: false,
    });
    const status = res.status();
    if (status === 0) throw new Error(`Network request failed: GET ${path}`);
    if (status !== expectedStatus) {
      const raw = await res.text().catch(() => '');
      throw new Error(`GET ${path} returned ${status} (expected ${expectedStatus}): ${raw.slice(0, 300)}`);
    }
    return { status, body: (await res.json()) as T };
  }

  /** POST request via page.request. */
  async postApi<T = unknown>(
    page: Page,
    path: string,
    data: unknown,
    expectedStatus = 200
  ): Promise<{ status: number; body: T }> {
    this.monitor.trackApiPost(path);
    const res = await page.request.post(`${process.env.API_BASE_URL || 'http://127.0.0.1:8000'}${path}`, {
      data,
      headers: { 'Content-Type': 'application/json' },
      timeout: 30_000,
      failOnStatusCode: false,
    });
    const status = res.status();
    if (status === 0) throw new Error(`Network request failed: POST ${path}`);
    if (status !== expectedStatus) {
      const raw = await res.text().catch(() => '');
      throw new Error(`POST ${path} returned ${status} (expected ${expectedStatus}): ${raw.slice(0, 300)}`);
    }
    return { status, body: (await res.json()) as T };
  }

  /** PATCH request via page.request. */
  async patchApi<T = unknown>(
    page: Page,
    path: string,
    data: unknown,
    expectedStatus = 200
  ): Promise<{ status: number; body: T }> {
    this.monitor.trackApiPatch(path);
    const res = await page.request.patch(`${process.env.API_BASE_URL || 'http://127.0.0.1:8000'}${path}`, {
      data,
      headers: { 'Content-Type': 'application/json' },
      timeout: 30_000,
      failOnStatusCode: false,
    });
    const status = res.status();
    if (status === 0) throw new Error(`Network request failed: PATCH ${path}`);
    if (status !== expectedStatus) {
      const raw = await res.text().catch(() => '');
      throw new Error(`PATCH ${path} returned ${status} (expected ${expectedStatus}): ${raw.slice(0, 300)}`);
    }
    return { status, body: (await res.json()) as T };
  }

  /** DELETE request via page.request. */
  async deleteApi<T = unknown>(page: Page, path: string, expectedStatus = 200): Promise<{ status: number; body: T }> {
    this.monitor.trackApiDelete(path);
    const res = await page.request.delete(`${process.env.API_BASE_URL || 'http://127.0.0.1:8000'}${path}`, {
      timeout: 30_000,
      failOnStatusCode: false,
    });
    const status = res.status();
    if (status === 0) throw new Error(`Network request failed: DELETE ${path}`);
    if (status !== expectedStatus) {
      const raw = await res.text().catch(() => '');
      throw new Error(`DELETE ${path} returned ${status} (expected ${expectedStatus}): ${raw.slice(0, 300)}`);
    }
    return { status, body: (await res.json()) as T };
  }

  // ───────── Locator resolution helpers ─────────────────────────────────

  private async resolveLocator(page: Page, target: string | Locator, role: string, label: string): Promise<Locator> {
    if (typeof target === 'string' && target.startsWith('[') && target.endsWith(']')) {
      return page.locator(target);
    }
    if (typeof target === 'string' && target.startsWith('/')) {
      return page.locator(`text=${target}`);
    }
    if (typeof target === 'string') {
      const labeled = page.getByLabel(target, { exact: true }).first();
      if ((await labeled.count()) > 0) return labeled;
      const altLabeled = page.getByLabel(target).first();
      if ((await altLabeled.count()) > 0) return altLabeled;
      const nameMatch = page.locator(`[name="${target}"]`).first();
      if ((await nameMatch.count()) > 0) return nameMatch;
      const placeholder = page.locator(`[placeholder*="${target}"]`).first();
      if ((await placeholder.count()) > 0) return placeholder;
      const roleMatch = page.locator(role, { name: target }).first();
      if ((await roleMatch.count()) > 0) return roleMatch;
      // Final fallback: case-insensitive, partial-text matching against
      // clickable elements (e.g. a dynamic "Place Order — $12.99" button).
      const targetRole = role === "button, a, [role=\"button\"]" ? "button" : "*";
      const partialText = page.getByRole(targetRole, { name: target }).first();
      if ((await partialText.count()) > 0) return partialText;
      return page.locator(`text=${target}`).first();
    }
    return target;
  }

  private async resolveInput(page: Page, target: string | Locator): Promise<{ locator: Locator; kind: string }> {
    if (typeof target === 'string') {
      const candidate = page.locator(`input[name="${target}"], input[autocomplete="${target}"]`).first();
      if ((await candidate.count()) > 0) return { locator: candidate, kind: `input[name="${target}"]` };
      return { locator: page.locator(`input[placeholder*="${target}"]`), kind: `input[placeholder*="${target}"]` };
    }
    return { locator: target, kind: 'locator' };
  }
}
