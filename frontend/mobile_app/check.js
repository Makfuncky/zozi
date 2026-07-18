const http = require('http');
const options = {
  host: 'localhost',
  port: 8082,
  path: '/'
};

const req = http.request(options, (res) => {
  let data = '';
  res.on('data', (chunk) => { data += chunk; });
  res.on('end', () => {
    console.log('Response length:', data.length);
    console.log('First 2000 chars:', data.substring(0, 2000));
  });
});

req.on('error', (e) => {
  console.error('Error:', e.message);
});

req.end();