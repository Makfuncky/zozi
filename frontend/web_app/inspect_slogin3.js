const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  const all = [];
  p.on('request', r => { if (!r.url().includes('geo') && !r.url().includes('favicon')) all.push('REQ ' + r.method() + ' ' + r.url().slice(0, 80)); });
  p.on('response', r => { if (!r.url().includes('geo') && !r.url().includes('favicon')) all.push('RES ' + r.status() + ' ' + r.url().slice(0, 80)); });
  p.on('pageerror', e => all.push('PE: ' + e.message));
  p.on('console', m => { if (m.type()==='error') all.push('CE: ' + m.text().slice(0,120)); });
  await p.goto('http://127.0.0.1:3000/supplier/login', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(2000);
  await p.fill('input[placeholder="Username"]', 'supplier@zozi.com');
  await p.fill('input[type="password"]', 'supplier123');
  await p.click('button:has-text("Sign In")');
  await p.waitForTimeout(4000);
  console.log('URL:', p.url());
  console.log(all.join('\n'));
  await b.close();
})();
