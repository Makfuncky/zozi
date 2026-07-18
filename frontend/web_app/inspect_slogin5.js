const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  p.on('pageerror', e => console.log('PE:', e.message));
  await p.goto('http://127.0.0.1:3000/supplier/login', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(1500);
  await p.fill('input[placeholder="Username"]', 'supplier@zozi.com');
  await p.fill('input[type="password"]', 'supplier123');
  await p.click('button:has-text("Sign In")');
  await p.waitForTimeout(4000);
  console.log('After signin URL:', p.url());
  // Directly navigate to add page (token should be in memory for this tab)
  await p.goto('http://127.0.0.1:3000/supplier/products/add', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(3000);
  console.log('Add page URL:', p.url());
  const redirected = p.url().includes('/login');
  console.log('Redirected to login?', redirected);
  if (!redirected) {
    const hasUpload = await p.locator('input[type="file"][accept*="image"]').count();
    console.log('Image file inputs on add page:', hasUpload);
  }
  await b.close();
})();
