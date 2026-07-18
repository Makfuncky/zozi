const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  const reqs = [];
  p.on('response', r => { if (r.url().includes('/api/') || r.url().includes('/auth')) reqs.push(r.status() + ' ' + r.url()); });
  await p.goto('http://127.0.0.1:3000/supplier/login', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(2000);
  await p.fill('input[placeholder="Username"]', 'supplier@zozi.com');
  await p.fill('input[type="password"]', 'supplier123');
  await p.click('button:has-text("Sign In")');
  await p.waitForTimeout(4000);
  console.log('URL:', p.url());
  const txt = await p.evaluate(() => document.body.innerText.slice(0, 300));
  console.log('BODY:', txt.replace(/\n+/g, ' | '));
  console.log('API CALLS:', JSON.stringify(reqs));
  await b.close();
})();
