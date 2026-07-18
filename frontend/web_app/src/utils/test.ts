/**
 * Test utilities for Playwright tests
 * Re-exports test from @playwright/test with custom setup
 */
import { test as baseTest } from "@playwright/test";

// Custom test with common fixtures
const test = baseTest.extend({
  // Add custom fixtures here if needed
});

export { test };
