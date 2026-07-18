const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  p.on('response', r => { if (r.url().includes('/auth/login')) console.log('AUTH RESP:', r.status(), JSON.stringify(r.headers()['content-type'])); });
  await p.goto('http://127.0.0.1:3000/supplier/login', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(1500);
  await p.fill('input[placeholder="Username"]', 'supplier@zozi.com');
  await p.fill('input[type="password"]', 'supplier123');
  await p.click('button:has-text("Sign In")');
  await p.waitForTimeout(5000);
  const tok = await p.evaluate(() => localStorage.getItem('access_token') || localStorage.getItem('token') || document.cookie.slice(0,100));
  console.log('TOKEN/Cookie:', tok);
  console.log('URL:', p.url());
  const txt = await p.evaluate(() => document.body.innerText.slice(0, 200).replace(/\n+/g,' | '));
  console.log('BODY:', txt);
  await b.close();
})();
