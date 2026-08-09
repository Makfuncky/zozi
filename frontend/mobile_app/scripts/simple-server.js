const fs = require('fs');
const http = require('http');
const path = require('path');

const ROOT = path.join(__dirname, '..', 'web-dist');
const PORT = process.env.PW_PORT || 8090;

const server = http.createServer((req, res) => {
  let url = decodeURIComponent(req.url.split('?')[0]);
  if (url === '/') url = '/index.html';
  let file = path.join(ROOT, url);
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    file = path.join(ROOT, 'index.html');
  }
  fs.readFile(file, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end('Not Found');
    } else {
      const ext = path.extname(file).slice(1);
      const types = {
        html: 'text/html',
        css: 'text/css',
        js: 'application/javascript',
        png: 'image/png',
        jpg: 'image/jpeg',
        json: 'application/json',
      };
      res.writeHead(200, { 'Content-Type': types[ext] || 'text/plain' });
      res.end(data);
    }
  });
});

server.listen(PORT, () => {
  console.log(`Serving web-dist on ${PORT}`);
});