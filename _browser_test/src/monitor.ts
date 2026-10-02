/**
 * Test monitor — the anti-green-signal guard.
 *
 * Every Playwright test MUST record the actions it performs. A test that only
 * opens the browser and asserts nothing is a "green-signal" test and will FAIL.
 *
 * Rule enforced on every test:
 *   (actions: click/fill/type/select/upload) +
 *   (api calls: get/post/patch/delete) +
 *   (assertions: expect(...))
 * must total > 0. A test with zero work raises an error at the end of the test.
 *
 * The monitor is injected per-test via `tests/fixtures.ts` and finalized in the
 * test's `after` hook. Tests record work by calling `monitor.track*()` on the
 * commands/workflows/verify instances, or by using the commands' built-in
 * recording.
 */

export interface RecordedAction {
  kind:
    | 'navigation'
    | 'click'
    | 'fill'
    | 'type'
    | 'select'
    | 'upload'
    | 'api-get'
    | 'api-post'
    | 'api-patch'
    | 'api-delete'
    | 'assert';
  target: string;
  at: number;
  stack?: string;
}

export class TestMonitor {
  private readonly actions: RecordedAction[] = [];
  private readonly testTitle: string;
  private finished = false;

  constructor(testTitle: string) {
    this.testTitle = testTitle;
  }

  private record(kind: RecordedAction['kind'], target: string): void {
    if (this.finished) {
      throw new Error(
        `Cannot record actions on "${this.testTitle}" after finalize() — ` +
        `a test should not record actions in its fixture "after" hook.`
      );
    }
    this.actions.push({
      kind,
      target,
      at: Date.now(),
      stack: new Error().stack?.split('\n').slice(2, 5).join('\n'),
    });
  }

  /** A page navigation (goto). */
  trackNavigation(target: string): void {
    this.record('navigation', target);
  }

  /** A user click / tap. */
  trackClick(target: string): void {
    this.record('click', target);
  }

  /** Filling a text field. */
  trackFill(target: string): void {
    this.record('fill', target);
  }

  /** Typing into a contenteditable / input (alias for fill). */
  trackType(target: string): void {
    this.record('type', target);
  }

  /** Selecting an option (dropdown). */
  trackSelect(target: string): void {
    this.record('select', target);
  }

  /** Uploading a file. */
  trackUpload(target: string): void {
    this.record('upload', target);
  }

  /** An API GET. */
  trackApiGet(target: string): void {
    this.record('api-get', target);
  }

  /** An API POST. */
  trackApiPost(target: string): void {
    this.record('api-post', target);
  }

  /** An API PATCH. */
  trackApiPatch(target: string): void {
    this.record('api-patch', target);
  }

  /** An API DELETE. */
  trackApiDelete(target: string): void {
    this.record('api-delete', target);
  }

  /** An assertion (expect(...)). */
  trackAssert(target: string): void {
    this.record('assert', target);
  }

  /**
   * Finalize: enforce the no-green-signal rule and report.
   *
   * @throws {Error} if the test performed zero meaningful work.
   */
  async finalize(): Promise<void> {
    this.finished = true;
    const summary: Record<string, number> = {};
    for (const a of this.actions) {
      summary[a.kind] = (summary[a.kind] ?? 0) + 1;
    }

    const hasUserAction =
      summary.click! + summary.fill! + summary.type! + summary.select! + summary.upload! > 0;
    const hasApi =
      summary['api-get']! + summary['api-post']! + summary['api-patch']! + summary['api-delete']! > 0;
    const hasAssert = summary.assert! > 0;
    const hasNavigation = summary.navigation! > 0;

    const error: string[] = [];
    if (!hasUserAction && !hasApi && !hasAssert) {
      error.push(
        'zero user actions (click/fill/type/select/upload), ' +
        'zero API calls, and zero assertions'
      );
    } else if (!hasAssert) {
      error.push('zero assertions — a test must assert observable outcomes');
    } else if (!hasUserAction && !hasApi && hasAssert) {
      error.push(
        'zero user actions AND zero API calls — an assertion-only test ' +
        'cannot verify anything (green-signal test)'
      );
    }

    if (error.length) {
      throw new Error(
        `Test "${this.testTitle}" is a green-signal test: it performed ` +
        `${error.join(', ')}.\n\nRecord work by calling monitor.track*() or by using ` +
        `the injected commands/workflows, and always assert with expect(...).\n\n` +
        `Action summary: ${JSON.stringify(summary)}`
      );
    }

    console.log(
      `[monitor] "${this.testTitle}" — ${this.actions.length} recorded actions: ` +
      `${JSON.stringify(summary)}`
    );
  }

  report(): string {
    const summary: Record<string, number> = {};
    for (const a of this.actions) {
      summary[a.kind] = (summary[a.kind] ?? 0) + 1;
    }
    return `Test "${this.testTitle}" — ${this.actions.length} actions: ${JSON.stringify(summary)}`;
  }

  /** Public getter for the test title used in error and summary messages. */
  getTitle(): string {
    return this.testTitle;
  }

  getActions(): ReadonlyArray<RecordedAction> {
    return [...this.actions];
  }
}

/**
 * Static pre-test scan (CI gate): ensures every spec file contains at least one
 * user-action call or assertion. Runs BEFORE `npx playwright test` when
 * invoked via scripts/pretest-check.ts.
 */
export async function preTestScan(testDir: string): Promise<{ scanned: number; failed: number; messages: string[] }> {
  const fs = await import('fs');
  const path = await import('path');

  const patterns = ['**/*.spec.ts', '**/*.test.ts'];
  const messages: string[] = [];
  let scanned = 0;
  let failed = 0;

  async function scanDir(dir: string): Promise<void> {
    const entries = await fs.promises.readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        await scanDir(fullPath);
      } else if (/\.spec\.ts$/.test(entry.name) || /\.test\.ts$/.test(entry.name)) {
        scanned++;
        const content = await fs.promises.readFile(fullPath, 'utf-8');
        const hasAction =
          /await page\.(goto|click|fill|type|press|check|uncheck|selectOption|upload|dblclick|hover)/.test(content) ||
          /\b(await |\b)(commands|workflows|ui)\./.test(content) ||
          /monitor\.(track|record)/.test(content) ||
          /page\.route\(/.test(content);
        const hasAssert = /expect\(/.test(content);
        if (!hasAction || !hasAssert) {
          failed++;
          messages.push(
            `SKIP/FAIL: ${path.relative(testDir, fullPath)} ` +
            `${!hasAction ? 'has no browser action (goto/click/fill/...' : ''} ` +
            `${!hasAssert ? 'has no expect(...) assertion' : ''}`
          );
        }
      }
    }
  }

  await scanDir(testDir);
  return { scanned, failed, messages };
}
