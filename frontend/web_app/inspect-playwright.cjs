const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  const r = await page.request.post('http://127.0.0.1:3000/api/auth/login', {
    json: { username: 'admin@zozi.com', password: 'admin123' }
  });
  console.log('Status:', r.status());
  console.log('Headers:');
  for (const [key, value] of Object.entries(r.headers())) {
    console.log(`  ${key}: ${value}`);
  }
  console.log('Body:', await r.text());

  // Also test with text body
  const r2 = await page.request.post('http://127.0.0.1:3000/api/auth/login', {
    text: JSON.stringify({ username: 'admin@zozi.com', password: 'admin123' })
  });
  console.log('\nText body status:', r2.status());
  console.log('Text body headers:');
  for (const [key, value] of Object.entries(r2.headers())) {
    console.log(`  ${key}: ${value}`);
  }
  console.log('Text body:', await r2.text());

  await browser.close();
})();
