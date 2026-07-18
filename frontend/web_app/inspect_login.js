const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('http://127.0.0.1:3000/login', { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(2500);
  const inputs = await p.$$eval('input', els => els.map(e => ({ t: e.type, n: e.name, ph: e.placeholder, id: e.id })));
  console.log('INPUTS:', JSON.stringify(inputs));
  const btns = await p.$$eval('button', els => els.map(e => e.textContent.trim()).filter(Boolean));
  console.log('BUTTONS:', JSON.stringify(btns));
  await b.close();
})();
