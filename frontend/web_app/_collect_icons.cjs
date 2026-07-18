const fs = require('fs');
const path = require('path');
function walk(d) {
  let r = [];
  for (const f of fs.readdirSync(d)) {
    const p = path.join(d, f);
    const st = fs.statSync(p);
    if (st.isDirectory()) {
      if (f === '.next' || f === 'node_modules') continue;
      r = r.concat(walk(p));
    } else if (/\.(ts|tsx)$/.test(f)) {
      r.push(p);
    }
  }
  return r;
}
const set = new Set();
const re = /import\s*\{([^}]+)\}\s*from\s*["']lucide-react["']/g;
for (const f of walk('src')) {
  const c = fs.readFileSync(f, 'utf8');
  let m;
  while ((m = re.exec(c))) {
    m[1].split(',').forEach((x) => {
      const n = x.replace(/as\s+\w+/, '').trim();
      if (n && n !== '*') set.add(n);
    });
  }
}
const names = [...set].sort();
console.log('COUNT ' + names.length);
console.log(names.join(','));
