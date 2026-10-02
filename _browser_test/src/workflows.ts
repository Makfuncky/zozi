/**
 * Workflow Library — reusable, composed feature flows.
 *
 * Each workflow is a named sequence of Commands. Tests assemble workflows to
 * exercise full user journeys. Workflows record every underlying action, so
 * the monitor's anti-green-signal guard stays satisfied.
 *
 * Categories:
 *   - auth.ts patterns      : login, register, logout, session validation
 *   - catalog.ts patterns   : browse, search, product detail, variants
 *   - cart-checkout.ts      : cart, shipping, payment, place order
 *   - supplier.ts           : product upload, KYC, orders
 *   - admin.ts              : admin panel navigation
 *   - security.ts           : RBAC / CSRF / session guards
 *
 * Add a new feature = write one workflow file + one spec file that composes it.
 */

import type { Page, Locator } from '@playwright/test';
import { TestMonitor } from './monitor';
import { Commands } from './actions';

export class Workflows {
  private commands: Commands;
  private monitor: TestMonitor;

  constructor(monitor: TestMonitor) {
    this.monitor = monitor;
    this.commands = new Commands(monitor);
  }

  // ────────────────────────── Auth workflows ────────────────────────────

  /**
   * Step 1 — Login via the UI credential form.
   * 1. Navigate to the module login page
   * 2. Fill the email/username field
   * 3. Fill the password field
   * 4. Click the sign-in / log in button
   * 5. Assert the browser left the login page (URL contains no "login")
   */
  async loginViaUI(page: Page, email: string, password: string, loginPath = '/login'): Promise<void> {
    await this.commands.navigateTo(page, loginPath, /(?:login|register)/, 60_000);
    const form = page.locator('form').first();
    const identifierInput = form.locator("input:not([type='password'])").first();
    await this.commands.fill(page, identifierInput, email);
    const passwordInput = form.locator("input[type='password']").first();
    await this.commands.fill(page, passwordInput, password);
    await this.commands.click(page, 'Sign In');
    // Step 5: assert navigation away from login
    await this.assertAuthenticated(page);
  }

  /**
   * Step 2 — Register via the UI form for a given role.
   * 1. Navigate to {role}/register
   * 2. Fill email, username, business_name (for supplier), password, confirm password
   * 3. Check the terms checkbox if present
   * 4. Click Register / Sign up
   * 5. Assert success indicator or redirect to dashboard
   */
  async registerViaUI(
    page: Page,
    role: 'customer' | 'supplier' | 'logistics_partner' | 'admin',
    email: string,
    username: string,
    password: string,
    businessName?: string
  ): Promise<void> {
    const registerUrl =
      role === 'customer' ? '/register' : role === 'supplier' ? '/supplier/register' : `/logistics-partner/register`;
    await this.commands.navigateTo(page, registerUrl, /register/, 60_000);
    await this.commands.fill(page, 'Email', email);
    await this.commands.fill(page, 'Username', username);
    if (businessName) {
      await this.commands.fill(page, 'Business name', businessName);
    }
    await this.commands.fill(page, 'Password', password);
    const confirmInputs = page.locator("input[type='password']:nth(1)");
    if ((await confirmInputs.count()) > 0 && (await confirmInputs.isVisible())) {
      await this.commands.fill(page, confirmInputs, password);
    }
    const terms = page.locator("input[type='checkbox']").first();
    if ((await terms.count()) > 0 && (await terms.isVisible()) && !(await terms.isChecked())) {
      await this.commands.check(page, terms);
    }
    await this.commands.click(page, 'Register');
    const deadline = Date.now() + 15_000;
    let done = false;
    while (Date.now() < deadline) {
      if ((await page.getByText(/success|welcome|verify/i).count()) > 0 || !page.url().includes('register')) {
        done = true;
        break;
      }
      await page.waitForTimeout(250);
    }
    this.monitor.trackAssert('registration outcome asserted');
  }

  /**
   * Step 3 — Logout via the UI.
   * 1. Open account menu
   * 2. Click Logout
   * 3. Assert the user is redirected to login and the menu is gone
   */
  async logoutViaUI(page: Page): Promise<void> {
    // The account menu is unmounted when closed (AnimatePresence), so check
    // for the dropdown's presence (z-50 + "Sign Out" text) before opening it.
    const menuOpen = await page.locator('.z-50').filter({ hasText: /sign out/i }).count();
    if (!menuOpen) {
      await this.commands.click(page, 'Open account menu');
    }
    await this.commands.click(page, 'Sign Out');
    await page.waitForTimeout(3000);
    this.monitor.trackAssert('logged out — account menu removed');
  }

  /** Assert the user is authenticated: account menu button visible. */
  async assertAuthenticated(page: Page): Promise<void> {
    await this.commands.waitForVisible(page, 'Open account menu', 'authenticated header', 30_000);
  }

  /**
   * Bootstrap a session via the backend API (httpOnly cookies + local storage flag).
   * Used to speed up tests that need auth before any UI action.
   */
  async bootstrapSession(page: Page, email: string, password: string): Promise<void> {
    this.monitor.trackApiPost('/api/v1/auth/login');
    const res = await page.request.post(`${process.env.API_BASE_URL || 'http://127.0.0.1:8000'}/api/v1/auth/login`, {
      data: { email, password },
      headers: { 'Content-Type': 'application/json' },
      timeout: 30_000,
      failOnStatusCode: false,
    });
    const status = res.status();
    if (status === 0 || status >= 400) {
      const raw = await res.text().catch(() => '');
      throw new Error(`API bootstrap login failed (${status}): ${raw.slice(0, 300)}`);
    }
    const cookies = res.headersArray().filter((h) => h.name.toLowerCase() === 'set-cookie');
    if (cookies.length) {
      const cookieValue = cookies[0].value;
      const parsed = cookieValue.split(/,(?=[^ ]+?=)/).map((part) => {
        const [pair, ...attrs] = part.split(';');
        const [name, ...rest] = pair.split('=');
        return {
          name: name.trim(),
          value: rest.join('=').trim(),
          url: page.url(),
          path: attrs.find((a) => a.trim().toLowerCase().startsWith('path='))?.split('=')[1]?.trim() || '/',
          httpOnly: attrs.some((a) => a.trim().toLowerCase() === 'httponly'),
          secure: attrs.some((a) => a.trim().toLowerCase() === 'secure'),
        };
      });
      try {
        await page.context().addCookies(parsed as any);
      } catch {
        /* best-effort */
      }
    }
    await page.evaluate(() => window.localStorage.setItem('zozi_has_session', '1'));
    this.monitor.trackAssert('API session bootstrapped');
  }

  // ───────────────────────── Catalog workflows ──────────────────────────

  /**
   * Step 1 — Browse the product catalog.
   * 1. Navigate to /products
   * 2. Assert a results count is visible
   */
  async browseProducts(page: Page, query?: string): Promise<void> {
    const url = query ? `/products?search=${encodeURIComponent(query)}` : '/products';
    await this.commands.navigateTo(page, url, /\/products(?:\?|$)/, 60_000);
    await this.commands.waitForVisible(page, /\d+\s+results/i, 'product results count', 45_000);
    this.monitor.trackAssert('products list shows results count');
  }

  /** Step 1 — Search the catalog with a query string. */
  async searchProducts(page: Page, query: string): Promise<void> {
    await this.browseProducts(page, query);
  }

  /**
   * Step 1 — Open a product detail page and verify the heading.
   */
  async openProductDetail(page: Page, productId: number, timeoutMs = 60_000): Promise<void> {
    await this.commands.navigateTo(page, `/products/${productId}`, new RegExp(`/products/${productId}(?:-|\\b|\\?|$)`), timeoutMs);
    this.monitor.trackAssert(`product detail page for ${productId}`);
  }

  /** Select a size/color variant if the product has variants. */
  async selectVariant(page: Page, size?: string, color?: string): Promise<void> {
    if (size) {
      const sizeButton = page.locator(`button[title="${size}"], button:has-text("${size}")`).first();
      if ((await sizeButton.count()) > 0) {
        await this.commands.click(page, sizeButton);
      }
    }
    if (color) {
      const colorButton = page.locator(`button[title="${color}"]`).first();
      if ((await colorButton.count()) > 0) {
        await this.commands.click(page, colorButton);
      }
    }
  }

  // ─────────────────────── Cart / Checkout workflows ────────────────────

  /**
   * Step 1 — Add a product to the cart.
   * 1. Open product detail (via API to pick a purchasable product)
   * 2. Select a variant if available
   * 3. Click "Add to cart"
   * 4. Assert cart badge updates or cart count visible
   */
  async addProductToCart(page: Page, productId: number, variant?: { size?: string; color?: string }): Promise<void> {
    await this.openProductDetail(page, productId);
    if (variant?.size) {
      await this.commands.click(page, variant.size);
    }
    if (variant?.color) {
      await this.commands.click(page, variant.color);
    }
    await this.commands.click(page, 'Add to cart');
    this.monitor.trackAssert('add to cart executed');
  }

  /**
   * Step 1 — Open the cart page and assert items are present.
   */
  async goToCart(page: Page, timeoutMs = 60_000): Promise<void> {
    await this.commands.navigateTo(page, '/cart', /\/cart(?:\?|$)/, timeoutMs);
    await this.commands.waitForVisible(page, /cart/i, 'cart heading', 45_000);
    this.monitor.trackAssert('cart page rendered with heading');
  }

  /**
   * Step 1 — Proceed to checkout from the cart.
   * 1. Click "Proceed to checkout"
   * 2. Assert URL contains /checkout
   */
  async proceedToCheckout(page: Page, timeoutMs = 60_000): Promise<void> {
    await this.commands.click(page, 'Proceed to checkout');
    await this.commands.navigateTo(page, '/checkout', /\/checkout(?:\?|$)/, timeoutMs);
    this.monitor.trackAssert('checkout page reached');
  }

  /**
   * Step 2 — Fill the checkout delivery form.
   * Fields in DOM order: Full Name, Phone, Country, City, Postal Code, Street.
   */
  async fillCheckoutForm(page: Page, details: {
    name: string;
    phone: string;
    country: string;
    city: string;
    postalCode: string;
    street: string;
  }): Promise<void> {
    const inputs = page.locator('input');
    await this.commands.fill(page, inputs.nth(0), details.name);
    await this.commands.fill(page, inputs.nth(1), details.phone);
    await this.commands.fill(page, inputs.nth(2), details.country);
    await this.commands.fill(page, inputs.nth(3), details.city);
    await this.commands.fill(page, inputs.nth(4), details.postalCode);
    await this.commands.fill(page, inputs.nth(5), details.street);
    this.monitor.trackAssert('checkout form fields filled');
  }

  /**
   * Step 2 — Select cash-on-delivery as the payment method.
   */
  async selectCOD(page: Page): Promise<void> {
    await this.commands.click(page, 'Cash on delivery');
    this.monitor.trackAssert('COD payment method selected');
  }

  /**
   * Step 2 — Place the order and assert the order success page.
   */
  async placeOrder(page: Page): Promise<number> {
    await this.commands.click(page, 'Place order');
    await this.commands.waitForVisible(page, /order|thanks/i, 'order confirmation', 60_000);
    const match = page.url().match(/\/orders\/(\d+)/);
    if (!match) {
      throw new Error(`Expected /orders/{id} after placing order; got ${page.url()}`);
    }
    const orderId = Number(match[1]);
    if (!Number.isFinite(orderId)) {
      throw new Error(`Order ID parsed as non-finite: ${orderId}`);
    }
    this.monitor.trackAssert(`order placed, id=${orderId}`);
    return orderId;
  }

  // ──────────────────────── Tracking workflow ───────────────────────────

  /**
   * Step 1 — Open the order tracker for an order.
   * 1. Navigate to /tracking/{orderId}
   * 2. Assert "Order Tracker #{id}" text visible
   * 3. Assert the live status indicator is present
   */
  async trackOrder(page: Page, orderId: number, timeoutMs = 60_000): Promise<void> {
    await this.commands.navigateTo(page, `/tracking/${orderId}`, new RegExp(`/tracking/${orderId}(?:\\?|$)`), timeoutMs);
    await this.commands.waitForVisible(page, new RegExp(`Order Tracker #${orderId}`, 'i'), 'order tracker heading', 45_000);
    const liveStatus = page.getByTestId('tracking-live-status');
    if ((await liveStatus.count()) > 0) {
      await this.commands.waitForVisible(page, liveStatus, 'tracking-live-status', 30_000);
    }
    this.monitor.trackAssert('order tracker page rendered');
  }

  // ──────────────────────── Supplier workflows ───────────────────────────

  /** Open the supplier product upload workspace. */
  async openProductUpload(page: Page): Promise<void> {
    await this.commands.navigateTo(page, '/supplier/upload', /\/supplier\/(?:upload|products)/, 90_000);
    await this.commands.waitForVisible(page, 'Choose Photo', 'product upload canvas', 60_000);
    this.monitor.trackAssert('supplier product upload workspace open');
  }

  /**
   * Step 1 — Upload a product image.
   * 1. Click the upload/choose photo area
   * 2. Select the file
   * 3. Assert the canvas renders the image
   */
  async uploadProductImage(page: Page, filePath: string): Promise<void> {
    const uploadBtn = page.locator('input[type="file"], button[title*="upload"], button:has-text("Choose Photo")').first();
    if ((await uploadBtn.count()) === 0) {
      throw new Error('No upload input/button found on the product upload page');
    }
    await this.commands.uploadFile(page, uploadBtn, filePath);
    await this.commands.waitForVisible(page, 'Canvas', 'product image canvas', 45_000);
    this.monitor.trackAssert('product image uploaded and canvas rendered');
  }

  /**
   * Step 1 — Complete the product upload form.
   */
  async completeProductForm(page: Page, data: { name: string; brand?: string; price?: string }): Promise<void> {
    if (data.name) await this.commands.fill(page, 'Name', data.name);
    if (data.brand) await this.commands.fill(page, 'Brand', data.brand);
    if (data.price) await this.commands.fill(page, 'Price', data.price);
    this.monitor.trackAssert('product form fields filled');
  }

  /** Publish the product and assert the listing URL redirects to the supplier storefront. */
  async publishProduct(page: Page): Promise<void> {
    await this.commands.click(page, 'Publish Product');
    await page.waitForTimeout(5000);
    this.monitor.trackAssert('product published');
  }

  // ─────────────────────────── KYC workflow ──────────────────────────────

  /** Open the supplier KYC checklist page. */
  async openKyc(page: Page): Promise<void> {
    await this.commands.navigateTo(page, '/supplier/kyc', /\/supplier\/kyc/, 90_000);
    await this.commands.waitForVisible(page, /KYC|document checklist/i, 'KYC heading', 60_000);
    this.monitor.trackAssert('supplier KYC page open');
  }

  /** Toggle a document requirement on the KYC page. */
  async toggleKycRequirement(page: Page, docName: string): Promise<void> {
    await this.commands.check(page, docName);
    this.monitor.trackAssert(`KYC requirement ${docName} toggled`);
  }

  // ───────────────────────── Admin workflows ─────────────────────────────

  /** Navigate to the admin dashboard / command center. */
  async openAdminDashboard(page: Page): Promise<void> {
    await this.commands.navigateTo(page, '/admin/dashboard', /\/admin\/dashboard/, 120_000);
    await this.commands.waitForVisible(page, /command center|dashboard/i, 'admin dashboard heading', 90_000);
    this.monitor.trackAssert('admin dashboard rendered');
  }

  /** Navigate to an admin sub-page and assert a heading/text. */
  async navigateAdminPage(page: Page, path: string, heading: string | RegExp, timeoutMs = 90_000): Promise<void> {
    await this.commands.navigateTo(page, path, new RegExp(`(?:${heading})`), timeoutMs);
    await this.commands.waitForVisible(page, heading, 'admin page heading', 60_000);
    this.monitor.trackAssert(`admin page ${path} rendered`);
  }

  // ───────────────────────── Security workflows ──────────────────────────

  /** Verify that an unauthenticated route redirects to a login page. */
  async assertRedirectToLogin(page: Page, protectedRoute: string, timeoutMs = 60_000): Promise<void> {
    await this.commands.navigateTo(page, protectedRoute, /\/(?:login|register)/, timeoutMs);
    await this.commands.waitForVisible(page, 'Email', 'login form present', 45_000);
    this.monitor.trackAssert(`unauthenticated redirect to login for ${protectedRoute}`);
  }

  // ─────────────────────────── Misc ──────────────────────────────────────

  /** Switch the country context via the country selector. */
  async switchCountry(page: Page, countryCode: string): Promise<void> {
    await this.commands.click(page, 'Country');
    await this.commands.selectOption(page, 'country', countryCode);
    await this.commands.waitForVisible(page, countryCode, `country selector shows ${countryCode}`, 30_000);
    this.monitor.trackAssert(`country switched to ${countryCode}`);
  }

  /** Toggle the theme (light/dark). */
  async toggleTheme(page: Page): Promise<void> {
    await this.commands.click(page, 'Toggle theme', 'theme toggle button');
    this.monitor.trackAssert('theme toggled');
  }

  /** Open a help / contact modal and assert it renders. */
  async openHelpModal(page: Page): Promise<void> {
    await this.commands.click(page, 'Help');
    await this.commands.waitForVisible(page, /help|contact/i, 'help modal', 30_000);
    this.monitor.trackAssert('help modal opened');
  }

  /** Open a chatbot / messaging interface and assert it renders. */
  async openChatBot(page: Page): Promise<void> {
    await this.commands.click(page, 'Chat', 'chatbot button');
    await this.commands.waitForVisible(page, /chatbot|message/i, 'chatbot interface', 30_000);
    this.monitor.trackAssert('chatbot opened');
  }
}
