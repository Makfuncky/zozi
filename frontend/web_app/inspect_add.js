const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push('PE: ' + e.message));
  await p.goto('http://127.0.0.1:3000/login', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(2000);
  await p.fill('input[placeholder="you@email.com"]', 'supplier@zozi.com');
  await p.fill('input[type="password"]', 'supplier123');
  await p.click('button:has-text("Sign In")');
  await p.waitForTimeout(4000);
  console.log('URL after signin:', p.url());
  // Look for error text
  const bodyText = await p.evaluate(() => document.body.innerText.slice(0, 500));
  console.log('BODY:', bodyText.replace(/\n+/g, ' | '));
  // Now go to add page
  await p.goto('http://127.0.0.1:3000/supplier/products/add', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(2500);
  console.log('Add URL:', p.url());
  const fileInputs = await p.$$eval('input[type=file]', els => els.map(e => ({ accept: e.accept, cls: e.className.slice(0,40) })));
  console.log('FILE INPUTS:', JSON.stringify(fileInputs));
  console.log('ERRORS:', JSON.stringify(errs));
  await b.close();
})();
