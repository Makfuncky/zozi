const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('http://127.0.0.1:3000/supplier/login', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(2000);
  const inputs = await p.$$eval('input', els => els.map(e => ({ t: e.type, ph: e.placeholder })));
  console.log('SUPPLIER LOGIN INPUTS:', JSON.stringify(inputs));
  const btns = await p.$$eval('button', els => els.map(e => e.textContent.trim()).filter(Boolean));
  console.log('SUPPLIER LOGIN BUTTONS:', JSON.stringify(btns));
  await b.close();
})();
