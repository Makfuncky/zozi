const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  p.on('pageerror', e => console.log('PAGEERROR:', e.message));
  p.on('console', m => { if (m.type()==='error') console.log('CONSOLE.ERR:', m.text().slice(0,200)); });
  await p.goto('http://127.0.0.1:3000/supplier/login', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(1500);
  // Intercept auth/login response
  await p.route('**/auth/login', async (route) => {
    const resp = await route.fetch();
    const body = await resp.text();
    console.log('AUTH LOGIN BODY:', body.slice(0, 400));
    await route.fulfill({ response: resp, body });
  });
  await p.fill('input[placeholder="Username"]', 'supplier@zozi.com');
  await p.fill('input[type="password"]', 'supplier123');
  await p.click('button:has-text("Sign In")');
  await p.waitForTimeout(4000);
  console.log('URL:', p.url());
  await b.close();
})();
