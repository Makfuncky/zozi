// codemod: convert numeric fontSize: N => fontSize: theme.fontSize.<token>
// Usage: node scripts/convert-fontsize-to-theme.js [path]
// Example: node scripts/convert-fontsize-to-theme.js frontend/mobile_app

const fs = require('fs');
const path = require('path');

const ROOT = process.argv[2] || process.cwd();
const EXTS = ['.ts', '.tsx', '.js', '.jsx'];

const TOKENS = {
  '3xl': 36,
  '2xl': 30,
  xl: 24,
  lg: 20,
  md: 17,
  base: 15,
  sm: 13,
  xs: 11,
};
const tokenEntries = Object.entries(TOKENS);

function closestToken(n) {
  let best = null;
  let bestDiff = Infinity;
  for (const [k, v] of tokenEntries) {
    const d = Math.abs(n - v);
    if (d < bestDiff) {
      bestDiff = d; best = k;
    }
  }
  return best;
}

function walk(dir, cb) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (['node_modules', '.git', '.expo'].includes(e.name)) continue;
      walk(full, cb);
    } else {
      cb(full);
    }
  }
}

const filesChanged = [];
walk(ROOT, (file) => {
  if (!EXTS.includes(path.extname(file))) return;
  // Only target mobile_app by default for safety if user passed a directory
  if (!file.includes('frontend' + path.sep + 'mobile_app') && !ROOT.includes('mobile_app')) return;
  let src = fs.readFileSync(file, 'utf8');
  let modified = src;

  // Skip files that already reference theme.fontSize in many places; still we replace numeric literals
  // Regex: fontSize: <number> optionally with spaces
  const re = /fontSize\s*:\s*([0-9]+(?:\.[0-9]+)?)/g;
  let match;
  let replacements = 0;
  const seen = new Set();
  while ((match = re.exec(src)) !== null) {
    const fullMatch = match[0];
    const num = Number(match[1]);
    // If this occurrence is already using theme.fontSize (rare), skip
    const start = match.index;
    const prefix = src.slice(Math.max(0, start - 20), start + fullMatch.length + 1);
    if (/theme\.fontSize/.test(prefix)) continue;

    const token = closestToken(num);
    if (!token) continue;
    // Build replacement
    const repl = `fontSize: theme.fontSize.${/^[0-9]/.test(token) ? "['" + token + "']" : token}`;
    // Avoid duplicate replacements at same position
    if (seen.has(start)) continue;
    seen.add(start);
    // Replace in modified (not src) to keep indexes valid
    modified = modified.replace(fullMatch, repl);
    replacements++;
  }

  if (replacements > 0 && modified !== src) {
    // Backup
    try {
      fs.writeFileSync(file + '.bak', src, 'utf8');
      fs.writeFileSync(file, modified, 'utf8');
      filesChanged.push({ file, replacements });
    } catch (err) {
      console.error('Failed writing', file, err);
    }
  }
});

console.log('Done. Files changed:', filesChanged.length);
for (const f of filesChanged) console.log(f.file, '=>', f.replacements, 'replacements');
console.log('Backups created with .bak extension');
